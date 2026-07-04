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
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "oc"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
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
    |> Enum.each(fn [api_key, user_id, faction_id] when is_integer(faction_id) ->
      api_call_id = Ecto.UUID.generate()
      Tornium.API.Store.create(api_call_id, 300)

      Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
        query(faction_id)
        |> Tornex.SpecQuery.put_key(api_key)
        |> Tornex.SpecQuery.put_key_owner(user_id)
        |> Tornex.Scheduler.Bucket.enqueue()
        |> Tornium.API.Store.insert(api_call_id)
      end)

      %{
        api_call_id: api_call_id,
        user_id: user_id,
        faction_id: faction_id
      }
      |> Tornium.Workers.OCUpdate.new(schedule_in: _seconds = 15)
      |> Oban.insert()
    end)

    :ok
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end

  @spec query(faction_id :: pos_integer()) :: Tornex.SpecQuery.t()
  def query(faction_id) when is_integer(faction_id) do
    Tornex.SpecQuery.new(nice: 0, resource_id: faction_id)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Crimes)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Basic)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Members)
  end
end
