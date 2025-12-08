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

defmodule Tornium.Workers.VerifyMember do
  @moduledoc """
  An Oban worker to verify a member of a server by their ID.

  WARNING: This is a temporary worker until all verification is migrated to Elixir.
  """

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :guild_processing,
    tags: ["guild", "verify"],
    unique: [
      period: :infinity,
      fields: [:worker, :args],
      keys: [:user_id, :server_id],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{
        args: %{"user_id" => user_id, "server_id" => server_id, "output_channel_id" => output_channel_id}
      })
      when is_nil(output_channel_id) or is_integer(output_channel_id) do
    {:ok, %Nostrum.Struct.Guild.Member{} = member} = Nostrum.Api.Guild.member(server_id, user_id)

    if not is_nil(output_channel_id) and output_channel_id != 0 do
      case Tornium.Guild.Verify.handle_on_join(server_id, member) do
        {:error, :api_key} ->
          nil

        {:error, :exclusion_role} ->
          nil

        {:error, {:config, _}} ->
          nil

        {status_atom, result, _server} when is_atom(status_atom) ->
          embed = Tornium.Guild.Verify.Message.message({status_atom, result}, member)
          Nostrum.Api.Message.create(output_channel_id, %{embeds: [embed]})
      end
    end

    :ok
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end
end
