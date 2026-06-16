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

      # TODO: handle the API error for an unverified user

      %{"error" => %{"code" => error_code}} when is_integer(error_code) ->
        {:cancel, {:api_error, error_code}}

      result when is_map(result) ->
        Nostrum.Api.Guild.member(guild_id, member_id)
        |> do_perform(guild_id, result)
    end
  end

  defp do_perform({:error, _error} = error, _guild_id, _api_call_result) do
    # TODO: Handle this case
    error
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
    |> Tornium.Guild.Verify.verify(member, force: false)

    :ok
  end
end
