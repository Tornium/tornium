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

defmodule Tornium.Workers.OverdoseUpdateScheduler do
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "faction"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{id: job_id} = _job) do
    Tornium.Schema.TornKey
    |> where([k], k.default == true and k.disabled == false and k.paused == false)
    |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
    |> where([k, u], not is_nil(u.faction_id) and u.faction_id != 0)
    |> where([k, u], u.faction_aa == true)
    |> distinct([k, u], u.faction_id)
    |> select([k, u, f], [k.api_key, u.tid, u.faction_id])
    |> Repo.all()
    |> Enum.each(fn [api_key, user_tid, faction_tid] when is_integer(faction_tid) ->
      query =
        Tornex.SpecQuery.new(key: api_key, key_owner: user_tid, nice: 10)
        |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Contributors)
        |> Tornex.SpecQuery.put_parameter(:stat, "drugoverdoses")
        |> Tornex.SpecQuery.put_parameter(:cat, "current")

      api_call_id = Ecto.UUID.generate()
      Tornium.API.Store.create(api_call_id, 300)

      Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
        query
        |> Tornex.Scheduler.Bucket.enqueue()
        |> Tornium.API.Store.insert(api_call_id)
      end)

      %{
        user_id: user_tid,
        faction_id: faction_tid,
        origin_job_id: job_id,
        api_call_id: api_call_id
      }
      |> Tornium.Workers.OverdoseUpdate.new(schedule_in: _seconds = 15)
      |> Oban.insert()
    end)

    :ok
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end
end
