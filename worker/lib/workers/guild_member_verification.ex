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

defmodule Tornium.Workers.GuildMemberVerification do
  @moduledoc """
  Verify a specific member of the Discord server.

  From the API data in tha API call ID, this worker will build and apply the verification
  changeset to the provided member in the provided Discord server. This worker also provides
  functionality for it to be called from non-Elixir components by providing `nil` for the
  `api_call_id` parameter. Optionally, a `token` parameter -- for a Discord interaction token
  -- can be provided to the worker (if there is no API call ID) for the worker to create a
  followup message to respond to the original slash command.
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
      keys: [:guild_id, :member_id],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"api_call_id" => nil, "guild_id" => guild_id, "member_id" => member_id} = args})
      when is_integer(guild_id) and is_integer(member_id) do
    # When there is no API call ID, it can be assumed that the job was invoked by a slash command, and we
    # need to respond as soon as possible to avoid excess backlog on the web server. So we should perform
    # the API call directly instead of through the bucket.
    guild =
      Tornium.Schema.Server
      |> where([s], s.sid == ^guild_id)
      |> Repo.one!()

    query = Tornium.User.update_query(member_id, Tornium.Guild.get_random_admin_key(guild), niceness: -20)
    api_call_result = Tornex.API.get(query)

    member = Nostrum.Api.Guild.member(guild_id, member_id)
    verification_result = do_perform(member, guild_id, api_call_result)

    # Once verification is complete, if a token has been provided in the job arguments we should respond to
    # the corresponding verification slash command or user command with the status of the verification attempt.
    interaction_token = Map.get(args, "token")

    if is_binary(interaction_token) do
      {:ok, fetched_member} = member

      Task.async(fn ->
        Nostrum.Api.Interaction.create_followup_message(interaction_token, %{
          embeds: [
            verification_result
            |> Tornium.Guild.Verify.Message.message(fetched_member)
            |> Map.from_struct()
          ],
          flags: 64
        })
      end)

      :ok
    else
      :ok
    end
  end

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "api_call_id" => api_call_id,
            "guild_id" => guild_id,
            "member_id" => member_id
          }
        } = _job
      )
      when is_integer(guild_id) and is_integer(member_id) do
    case Tornium.API.Store.pop(api_call_id) do
      nil ->
        {:cancel, :invalid_call_id}

      :expired ->
        {:cancel, :expired}

      :not_ready ->
        # This uses :error instead of :snooze to allow for an easy cap on the number of retries
        {:error, :not_ready}

      result when is_map(result) ->
        do_perform(member_id, guild_id, result)

        :ok
    end
  end

  @spec do_perform(
          {:ok, Nostrum.Struct.Guild.Member.t()} | Nostrum.Api.error() | pos_integer(),
          guild_id :: pos_integer(),
          api_call_result :: map()
        ) :: Tornium.Guild.Verify.verification_result() | Nostrum.Api.error()
  defp do_perform(_member, _guild_id, %{"error" => %{"code" => error_code}} = _api_call_result)
       when is_integer(error_code) and error_code not in [6] do
    {:cancel, {:api_error, error_code}}
  end

  defp do_perform(member_id, guild_id, api_call_result) when is_integer(member_id) do
    Nostrum.Api.Guild.member(guild_id, member_id)
    |> do_perform(guild_id, api_call_result)
  end

  defp do_perform({:error, _error} = error, _guild_id, _api_call_result) do
    # TODO: Handle this case
    error
  end

  defp do_perform(
         {:ok, %Nostrum.Struct.Guild.Member{} = member},
         guild_id,
         %{"error" => %{"code" => 6}} = _api_call_result
       ) do
    # This error would occur when the user is not verified. Since we've already performed
    # the API call, we can skip some of the code in verify/3 and just build and perform the
    # changes.
    guild =
      Tornium.Schema.Server
      |> where([s], s.sid == ^guild_id)
      |> Repo.one!()

    config = Tornium.Guild.Verify.Config.validate(guild)

    {:error, %Tornium.API.Error{code: 6}}
    |> Tornium.Guild.Verify.build_changes(config, member)
    |> Tornium.Guild.Verify.perform_changes(guild, member)

    # As skipping the unnecessary code in verify/3 also skips the :telemetry logging, we need
    # to do that ourselves here.
    Tornium.Guild.Verify.log({:error, %Tornium.API.Error{code: 6}, guild}, member)

    :ok
  end

  defp do_perform({:ok, %Nostrum.Struct.Guild.Member{user_id: member_id} = member}, guild_id, api_call_result) do
    {:ok, %Tornium.Schema.User{discord_id: ^member_id}} =
      Tornex.SpecQuery.new()
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Id.Profile)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Id.Discord)
      |> Tornex.SpecQuery.parse(api_call_result)
      |> Tornium.User.update_data()

    Tornium.Schema.Server
    |> where([s], s.sid == ^guild_id)
    |> Repo.one!()
    |> Tornium.Guild.Verify.verify(member, force?: false)
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end
end
