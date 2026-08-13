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

defmodule Tornium.Workers.ServerRefreshScheduler do
  @moduledoc """
  Scheduler for updating all servers and deleting server that don't have the Tornium bot on it anymore.

  This will chunk the servers by the number of pages of users it has (with a limit of 1000) to spread the Discord
  API calls across the entire hour.
  """

  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "guild"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @chunk_size 25

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    guilds = Tornium.Discord.fetch_all_guilds(limit: 1000, with_counts: true)
    guild_ids = Enum.map(guilds, & &1.id)

    guild_ids
    |> Enum.chunk_every(@chunk_size)
    |> Enum.with_index()
    |> Enum.each(fn {guild_id_chunk, index} when is_list(guild_id_chunk) and is_integer(index) ->
      # We want to refresh each server with increasing delay to stagger their executions and not
      # use too much of the Discord ratelimit at a time.
      guild_id_chunk
      |> Enum.map(fn guild_id ->
        Tornium.Workers.ServerRefresh.new(%{guild_id: guild_id}, schedule_in: _seconds = index * 60)
      end)
      |> Oban.insert_all()
    end)

    guild_ids
    |> get_servers_pending_deletion()
    |> Tornium.Schema.Server.delete_servers()

    :ok
  end

  @spec get_servers_pending_deletion(found_server_ids :: [pos_integer()]) :: [pos_integer()]
  defp get_servers_pending_deletion(found_server_ids) when is_list(found_server_ids) and found_server_ids != [] do
    Tornium.Schema.Server
    |> select([s], s.sid)
    |> where([s], s.sid not in ^found_server_ids)
    |> Repo.all()
  end

  defp get_servers_pending_deletion([] = _found_server_ids) do
    []
  end
end
