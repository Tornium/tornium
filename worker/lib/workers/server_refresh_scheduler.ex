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

  require Logger
  alias Tornium.Schema.ServerAttackConfig
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 5,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "guild"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    guilds = Tornium.Discord.fetch_all_guilds([], with_counts: true)
    guild_ids = Enum.map(guilds, & &1.id)

    # TODO: Refreshing found servers

    with {count, servers_pending_deletion} when count > 0 <- get_servers_pending_deletion(guild_ids) do
      Tornium.Schema.Server.delete_servers(servers_pending_deletion)
    end

    :ok
  end

  @spec get_servers_pending_deletion(found_server_ids :: [pos_integer()]) :: {non_neg_integer(), [pos_integer()]}
  defp get_servers_pending_deletion(found_server_ids) when is_list(found_server_ids) and found_server_ids != [] do
    Tornium.Schema.Server
    |> select([s], s.sid)
    |> where([s], s.sid not in ^found_server_ids)
    |> update([s], set: [notifications_config_id: nil])
    |> Repo.update_all([])
  end
end
