# Copyright (C) 2021-2025 tiksan
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

defmodule Tornium.Workers.GuildVerification do
  @moduledoc """
  Verify all members of the Discord server.
  """

  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :guild_processing,
    tags: ["guild"],
    unique: [
      period: :infinity,
      fields: [:worker, :args],
      keys: [:guild_id],
      states: :incomplete
    ]

  @api_query_timeout 300

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"guild_id" => guild_id, "after" => after_id}} = _job)
      when is_integer(guild_id) and is_integer(after_id) do
    guild =
      Tornium.Schema.Server
      |> where([s], s.sid == ^guild_id)
      |> Repo.one!()

    case Tornium.Guild.Verify.Config.validate(guild) do
      %Tornium.Guild.Verify.Config{} ->
        do_perform(guild, after_id)

      {:error, verification_config_error} ->
        :telemetry.execute([:tornium, :guild, :verify, :config_error], %{}, %{
          guild_id: guild_id,
          user_id: nil,
          error: verification_config_error
        })

        {:cancel, verification_config_error}
    end
  end

  defp do_perform(%Tornium.Schema.Server{sid: guild_id, admins: guild_admins} = guild, after_id) do
    # We want to maximize the number of users updated at once. We should overfetch the list of
    # server members as many members should have been updated recently and not require a Torn
    # API call to verify. However, for larger servers with more admins, we need to cap the
    # chunk size to 1000 as that's Discord's limit.
    chunk_size = min(length(guild_admins) * 50, 1000)

    {:ok, members} = Nostrum.Api.Guild.members(guild_id, limit: chunk_size, after: after_id)
    member_ids = Enum.map(members, & &1.user_id)

    users =
      Tornium.Schema.User
      |> where([u], u.discord_id in ^member_ids)
      |> Repo.all()
      |> Enum.map(&{&1.discord_id, &1})
      |> Map.new()

    # If Discord provides as many members as requested by the chunk size, that indicates that
    # there are likely more members in the server and another iteration is required.
    more_members? = length(members) == chunk_size
    next_after_id = do_perform_members(members, more_members?, users, guild, length(guild_admins) * 10)

    if is_nil(next_after_id) do
      :ok
    else
      # We want to spawn a new job to perform verification from the provided next_after_id
      # using Oban's recursive jobs. See https://oban.hexdocs.pm/recursive-jobs.html
      schedule(guild, after: next_after_id)
    end
  end

  @spec do_perform_members(
          members :: [Nostrum.Struct.Guild.Member.t()],
          more_members? :: boolean(),
          users :: %{pos_integer() => Tornium.Schema.User.t()},
          guild :: Tornium.Schema.Server.t(),
          api_call_count :: non_neg_integer(),
          max_api_call_count :: pos_integer()
        ) :: pos_integer() | nil
  defp do_perform_members(members, more_members?, users, guild, api_call_count \\ 0, max_api_call_count)

  defp do_perform_members(
         [] = _members,
         _more_members?,
         _users,
         %Tornium.Schema.Server{} = _guild,
         _api_call_count,
         _max_api_call_count
       ) do
    # This is mostly impossible except if the member(s) after the after parameter leaves
    # the server between the previous iteration of verification and this. We can assume
    # this to be the end of verification.
    nil
  end

  defp do_perform_members(
         [%Nostrum.Struct.Guild.Member{user_id: member_id} = member] = _members,
         more_members?,
         users,
         %Tornium.Schema.Server{} = guild,
         api_call_count,
         max_api_call_count
       )
       when is_map(users) and is_integer(api_call_count) and
              is_integer(max_api_call_count) and api_call_count >= max_api_call_count do
    # As we are currently on the last member in the provided list, we want to verify the
    # user if we can without performing an API call. If we are unable to do so, we should
    # let this member be the first member in the next iteration.  If the user is not
    # verified, we must perform an API call, and this member would be the first again.
    user = Map.get(users, member_id, nil)

    if is_nil(user) or requires_api_call?(user) do
      # Since the user is not verified/in the database or hasn't been updated, we want to 
      # include this user as the first in the next iteration of verification.
      member_id - 1
    else
      # Since the user is verified and has been updated recently, we can just verify them.
      # If there are no more members in the server, this is the end of verification for the
      # Discord server; otherwise, this is the after parmeter for the next iteration of
      # verification.
      {true, _} = verify_or_schedule({member, user}, guild)

      if more_members?, do: member_id, else: nil
    end
  end

  defp do_perform_members(
         [%Nostrum.Struct.Guild.Member{user_id: member_id} = member] = _members,
         more_members?,
         users,
         %Tornium.Schema.Server{} = guild,
         api_call_count,
         max_api_call_count
       )
       when is_map(users) and is_integer(api_call_count) and
              is_integer(max_api_call_count) do
    # As we are current on the last member in the provided list without reaching the maximum
    # API call count, we can perform an API call to update the user if necessary before
    # verifying the member.
    user = Map.get(users, member_id, nil)
    verify_or_schedule({member, user}, guild)

    # If there are no more members in this server, this is the end of verification for the
    # Discord server. Otherwise, this member is the after parameter for the next iteration
    # of verification.
    if more_members?, do: member_id, else: nil
  end

  defp do_perform_members(
         [%Nostrum.Struct.Guild.Member{user_id: member_id} = member | remaining_members] = _members,
         more_members?,
         users,
         %Tornium.Schema.Server{} = guild,
         api_call_count,
         max_api_call_count
       )
       when is_map(users) and is_map_key(users, member_id) and is_integer(api_call_count) and
              is_integer(max_api_call_count) and api_call_count >= max_api_call_count do
    # As the current API call count is at the maximum count, we can not make any more API
    # calls. Instead, we can continue verifying members until we reach a member we are unable
    # to verify without an API call.
    %Tornium.Schema.User{} = user = Map.fetch!(users, member_id)

    if requires_api_call?(user) do
      # We want to include this Discord member as the first user when the next iteration of
      # verification of this Discord server runs. But we can't make an API call for this as
      # we'd be making too many API calls.
      member_id - 1
    else
      # Since we don't need to an API call to verify this member, we can verify this member
      # and move on to the next one.
      {true, _} = verify_or_schedule({member, user}, guild)

      do_perform_members(remaining_members, more_members?, users, guild, api_call_count, max_api_call_count)
    end
  end

  defp do_perform_members(
         [%Nostrum.Struct.Guild.Member{user_id: member_id} = _member | _remaining_members] = _members,
         _more_members?,
         users,
         %Tornium.Schema.Server{} = _guild,
         api_call_count,
         max_api_call_count
       )
       when is_map(users) and not is_map_key(users, member_id) and is_integer(api_call_count) and
              is_integer(max_api_call_count) and api_call_count >= max_api_call_count do
    # When the Discord member is not verified, we need to make an API call to verify the member.
    # Since we can't perform any more API calls, this Discord member should be the first user
    # on the next iteration of verification for this Discord server.
    member_id - 1
  end

  defp do_perform_members(
         [%Nostrum.Struct.Guild.Member{user_id: member_id} = member | remaining_members] = _members,
         more_members?,
         users,
         %Tornium.Schema.Server{} = guild,
         api_call_count,
         max_api_call_count
       )
       when is_map(users) and is_map_key(users, member_id) and is_integer(api_call_count) and
              is_integer(max_api_call_count) do
    # As we are below the maximum API call count, we should make an API call for the member if
    # they haven't been updated recently. Otherwise, we can just immediatley verify the member.
    %Tornium.Schema.User{} = user = Map.fetch!(users, member_id)

    case verify_or_schedule({member, user}, guild) do
      {true, _} ->
        # The user was verified immediately without an API call.
        do_perform_members(remaining_members, more_members?, users, guild, api_call_count, max_api_call_count)

      {false, _} ->
        # The user is being verified later after an API call is made.
        do_perform_members(remaining_members, more_members?, users, guild, api_call_count + 1, max_api_call_count)
    end
  end

  defp do_perform_members(
         [%Nostrum.Struct.Guild.Member{user_id: member_id} = member | remaining_members] = _members,
         more_members?,
         users,
         %Tornium.Schema.Server{} = guild,
         api_call_count,
         max_api_call_count
       )
       when is_map(users) and not is_map_key(users, member_id) do
    # Since the Discord member ID is not in map of Torn users, the user is not verified. This
    # would require an API call to try to determine the Torn user for the Discord ID.
    verify_or_schedule({member, nil}, guild)

    do_perform_members(remaining_members, more_members?, users, guild, api_call_count + 1, max_api_call_count)
  end

  @spec requires_api_call?(user :: Tornium.Schema.User.t()) :: boolean()
  defp requires_api_call?(%Tornium.Schema.User{last_refresh: last_refresh} = _user) do
    one_hour_ago = DateTime.utc_now() |> DateTime.add(-1, :hour)

    # If the user was updated less than one hour ago, we can verify the user without trying to
    # make an API call to update the user's data. Otherwise, the user was updated too far in
    # the past, so we should update the user's data before verifying.
    DateTime.compare(last_refresh, one_hour_ago) != :gt
  end

  @spec verify_or_schedule(
          user_data :: {member :: Nostrum.Struct.Guild.Member.t(), user :: Tornium.Schema.User.t() | nil},
          guild :: Tornium.Schema.Server.t()
        ) ::
          {true,
           {:ok, Nostrum.Struct.Guild.Member.t(), Tornium.Schema.Server.t()} | Tornium.Guild.Verify.verification_error()}
          | {false, Oban.Job.t()}
  defp verify_or_schedule(
         {%Nostrum.Struct.Guild.Member{} = member, %Tornium.Schema.User{} = user} = _user_data,
         %Tornium.Schema.Server{} = guild
       ) do
    if requires_api_call?(user) do
      # The user was updated too far in the past, so we should pass this to the other clause of
      # the function to update the user's data before verifying the user.
      {false, verify_or_schedule({member, nil}, guild)}
    else
      # The user was updated less than one hour ago, so we can verify the user without trying to
      # make an API call to update the user's data.
      {true, Tornium.Guild.Verify.verify(guild, member)}
    end
  end

  defp verify_or_schedule(
         {%Nostrum.Struct.Guild.Member{user_id: member_id} = _member, user},
         %Tornium.Schema.Server{sid: guild_id} = guild
       )
       when is_nil(user) do
    # The user was updated more than one hour ago or the user was not in the database (likely
    # because the user is not verified or not known to be verified), so we should make an API
    # call to update the user's data and then try to verify the user.

    query = Tornium.User.update_query(member_id, Tornium.Guild.get_random_admin_key(guild), niceness: 20)

    api_call_id = Ecto.UUID.generate()
    Tornium.API.Store.create(api_call_id, @api_query_timeout)

    Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
      query
      |> Tornex.Scheduler.Bucket.enqueue(timeout: @api_query_timeout * 1_000)
      |> Tornium.API.Store.insert(api_call_id)
    end)

    %{
      api_call_id: api_call_id,
      member_id: member_id,
      guild_id: guild_id
    }
    |> Tornium.Workers.GuildMemberVerification.new(schedule_in: _seconds = 15)
    |> Oban.insert()
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end

  @doc """
  Schedule verification of all members of a Discord server.

  ## Options
    * `:after` - the highest Discord member ID from the previous page (default: `0`)
  """
  @spec schedule(guild :: pos_integer() | Tornium.Schema.Server.t(), opts :: keyword()) ::
          {:ok, Oban.Job.t()} | {:error, term()}
  def schedule(guild, opts \\ [])

  def schedule(guild, opts) when is_integer(guild) do
    Tornium.Schema.Server
    |> where([s], s.sid == ^guild)
    |> Repo.one!()
    |> schedule(opts)
  end

  def schedule(%Tornium.Schema.Server{sid: guild_id, admins: admins} = guild, opts)
      when is_integer(guild_id) and admins != [] do
    case Tornium.Guild.Verify.Config.validate(guild) do
      %Tornium.Guild.Verify.Config{} ->
        %{guild_id: guild_id, after: Keyword.get(opts, :after, 0)}
        |> new()
        |> Oban.insert()

      {:error, _} = error ->
        error
    end
  end
end
