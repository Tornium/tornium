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

defmodule Tornium.Workers.OCCPRUpdateScheduler do
  require Logger
  alias Tornium.Repo
  import Ecto.Query

  @batch_limit 100

  use Oban.Worker,
    max_attempts: 1,
    priority: 3,
    queue: :scheduler,
    tags: ["scheduler", "oc"],
    unique: [
      period: :infinity,
      states: [:available, :executing, :retryable, :scheduled]
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{id: job_id, args: %{"after" => after_id}} = _job) do
    users =
      Tornium.Schema.TornKey
      |> where([k], k.default == true)
      |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
      |> where([k, u], not is_nil(u.faction_id) and u.faction_id != 0)
      |> where([k, u], u.faction_aa == true)
      |> join(:inner, [k, u], f in assoc(u, :faction), on: f.tid == u.faction_id)
      |> where([k, u, f], f.has_migrated_oc == true)
      |> join(:left, [k, u, f], s in assoc(u, :settings), on: s.guid == u.settings_id)
      |> where([k, u, f, s], is_nil(s) or s.cpr_enabled == true)
      |> where([k, u, f, s], u.tid > ^after_id)
      |> select([k, u, f, s], [k.api_key, u.tid, u.faction_id])
      |> limit([k, u, f, s], @batch_limit)
      |> order_by([k, u, f, s], asc: u.tid)
      |> Repo.all()

    Enum.each(users, fn [api_key, user_tid, faction_tid]
                        when is_binary(api_key) and is_integer(user_tid) and is_integer(faction_tid) ->
      request = %Tornex.Query{
        resource: "v2/faction",
        resource_id: faction_tid,
        key: api_key,
        selections: ["crimes", "members"],
        key_owner: user_tid,
        nice: 20,
        params: [cat: "recruiting"]
      }

      api_call_id = Ecto.UUID.generate()
      Tornium.API.Store.create(api_call_id, 300)

      Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
        request
        |> Tornex.Scheduler.Bucket.enqueue()
        |> Tornium.API.Store.insert(api_call_id)
      end)

      %{
        user_tid: user_tid,
        faction_tid: faction_tid,
        origin_job_id: job_id,
        api_call_id: api_call_id
      }
      |> Tornium.Workers.OCCPRUpdate.new(schedule_in: _seconds = 15)
      |> Oban.insert()
    end)

    case List.last(users) do
      nil ->
        nil

      [_api_key, user_tid, _faction_tid] ->
        %{after: user_tid}
        |> Tornium.Workers.OCCPRUpdateScheduler.new(schedule_in: _seconds = 600)
        |> Oban.insert()
    end

    :ok
  end

  @impl Oban.Worker
  def perform(%Oban.Job{id: _job_id, args: _args} = job) do
    perform(%Oban.Job{job | args: %{"after" => 0}})
  end
end
