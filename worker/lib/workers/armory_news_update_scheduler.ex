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

defmodule Tornium.Workers.ArmoryNewsUpdateScheduler do
  @moduledoc """
  A scheduler to spawn `Tornium.Workers.ArmoryNewsUpdate` for each faction with at least one AA key.
  """

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
  def perform(%Oban.Job{} = _job) do
    Tornium.Schema.TornKey
    |> where([k], k.default == true and k.disabled == false and k.paused == false)
    |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
    |> where([k, u], not is_nil(u.faction_id) and u.faction_id != 0)
    |> where([k, u], u.faction_aa == true)
    |> distinct([k, u], u.faction_id)
    |> select([k, u, f], [k.api_key, u.tid, u.faction_id])
    |> Repo.all()
    |> Enum.each(fn [api_key, user_tid, faction_tid] when is_integer(faction_tid) ->
      schedule_faction(api_key, user_tid, faction_tid)
    end)

    :ok
  end

  @doc """
  Schedule an armory news update for a specific faction.

  This will use a random AA member's API key.
  """
  @spec schedule_faction(faction_id :: integer()) :: {:ok, Oban.Job.t()} | {:error, Oban.Job.changeset() | term()}
  def schedule_faction(faction_id) when is_integer(faction_id) do
    api_key_result =
      Tornium.Schema.TornKey
      |> where([k], k.default == true and k.disabled == false and k.paused == false)
      |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
      |> where([k, u], u.faction_id == ^faction_id and u.faction_aa == true)
      |> select([k, u, f], [k.api_key, u.tid])
      |> order_by(fragment("RANDOM()"))
      |> first()
      |> Repo.one()

    case api_key_result do
      [api_key, user_id] ->
        schedule_faction(api_key, user_id, faction_id)

      _ ->
        {:error, "Missing AA key"}
    end
  end

  @doc """
  Schedule an armory news update for a specific faction using a particular AA API key
  """
  @spec schedule_faction(api_key :: String.t(), user_id :: non_neg_integer(), faction_id :: non_neg_integer()) ::
          {:ok, Oban.Job.t()} | {:error, Oban.Job.changeset() | term()}
  def schedule_faction(api_key, user_id, faction_id)
      when is_binary(api_key) and is_integer(user_id) and is_integer(faction_id) do
    latest_faction_usage =
      Tornium.Schema.ArmoryUsage
      |> where([u], u.faction_id == ^faction_id)
      |> order_by([u], desc: u.timestamp)
      |> limit([u], 1)
      |> Repo.one()

    query =
      Tornex.SpecQuery.new(key: api_key, key_owner: user_id, nice: 10)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.News)
      |> Tornex.SpecQuery.put_parameter(:cat, "armoryAction")

    query =
      case latest_faction_usage do
        %Tornium.Schema.ArmoryUsage{timestamp: %DateTime{} = timestamp} ->
          # We want to ensure that the latest timestamp from the armory usage logs is within seven day of now to
          # ensure we aren't pulling too much data from the API
          timestamp =
            DateTime.utc_now()
            |> DateTime.add(-7, :day)
            |> then(&[&1, timestamp])
            |> Enum.max(DateTime)

          # We do not want to increment the from parameter to avoid missing data occurring at the same second.
          # Data already in the database will be handled by an on conflict statement.
          query
          |> Tornex.SpecQuery.put_parameter(:from, DateTime.to_unix(timestamp, :second))
          |> Tornex.SpecQuery.put_parameter(:sort, "asc")

        nil ->
          query
      end

    api_call_id = Ecto.UUID.generate()
    Tornium.API.Store.create(api_call_id, 300)

    Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
      query
      |> Tornex.Scheduler.Bucket.enqueue()
      |> Tornium.API.Store.insert(api_call_id)
    end)

    %{
      user_id: user_id,
      faction_id: faction_id,
      api_call_id: api_call_id
    }
    |> Tornium.Workers.ArmoryNewsUpdate.new(schedule_in: _seconds = 15)
    |> Oban.insert()
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end
end
