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

  @chunk_size 5

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    guilds = Tornium.Discord.fetch_all_guilds(with_counts: true)
    guild_ids = Enum.map(guilds, & &1.id)

    guilds
    |> Enum.map(fn %Nostrum.Struct.Guild{} = guild ->
      # TODO: Create a new oban job
      nil
    end)
    |> Enum.chunk_every(@chunk_size)
    |> Enum.with_index()
    |> Enum.each(fn {guilds, index} when is_list(guilds) and is_integer(index) ->
      # TODO: Insert the created Oban jobs with an increasing delay to stagger their executions
      nil
    end)

    {_count, servers_pending_deletion} = get_servers_pending_deletion(guild_ids)
    Tornium.Schema.Server.delete_servers(servers_pending_deletion)

    :ok
  end

  @spec get_servers_pending_deletion(found_server_ids :: [pos_integer()]) :: {non_neg_integer(), [pos_integer()]}
  defp get_servers_pending_deletion(found_server_ids) when is_list(found_server_ids) and found_server_ids != [] do
    Tornium.Schema.Server
    |> select([s], s.sid)
    |> where([s], s.sid not in ^found_server_ids)
    |> Repo.all()
  end
end
