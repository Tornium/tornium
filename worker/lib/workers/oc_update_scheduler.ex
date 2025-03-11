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

defmodule Tornium.Workers.OCUpdateScheduler do
  require Logger
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "oc"],
    unique: [
      period: :infinity,
      states: [:available, :executing, :retryable, :scheduled]
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    Tornium.Schema.TornKey
    |> where([k], k.default == true)
    |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
    |> where([k, u], not is_nil(u.faction_id) and u.faction_id != 0)
    |> where([k, u], u.faction_aa == true)
    |> distinct([k, u], u.faction_id)
    |> join(:inner, [k, u], f in assoc(u, :faction), on: f.tid == u.faction_id)
    |> where([k, u, f], f.has_migrated_oc == true)
    |> select([k, u, f], [k.api_key, u.tid, u.faction_id])
    |> Repo.all()
    |> Enum.map(fn [api_key, user_tid, faction_tid] when is_integer(faction_tid) ->
      %{
        api_key: api_key,
        user_tid: user_tid,
        faction_tid: faction_tid
      }
      |> Tornium.Workers.OCUpdate.new()
      |> Oban.insert()
    end)

    :ok
  end
end
