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

defmodule Tornium.Workers.ActiveWarfareUpdate do
  @moduledoc """
  Update all chains (and in the future, other warfare) that are active or have recently completed.
  """

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction"]

  import Ecto.Query
  alias Tornium.Repo

  @api_query_timeout 300
  @api_query_limit 100

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"api_call_id" => api_call_id} = args} = _job) when not is_nil(api_call_id) do
    case Tornium.API.Store.pop(api_call_id) do
      nil ->
        {:cancel, :invalid_call_id}

      :expired ->
        {:cancel, :expired}

      :not_ready ->
        # This uses :error instead of :snooze to allow for an easy cap on the number of retries
        {:error, :not_ready}

      %{"error" => %{"code" => error_code}} when is_integer(error_code) ->
        {:cancel, {:api_error, error_code}}

      result when is_map(result) ->
        do_perform(result, Map.get(args, "seen_chain_ids"))
    end
  end

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    schedule()
  end

  @spec do_perform(api_call_result :: map(), seen_chain_ids :: [pos_integer()]) :: Oban.Worker.result()
  defp do_perform(api_call_result, seen_chain_ids \\ []) when is_map(api_call_result) and is_list(seen_chain_ids) do
    %{
      Torngen.Client.Path.Faction.Warfarechains => %{
        FactionWarfareChainsResponse => %Torngen.Client.Schema.FactionWarfareChainsResponse{warfarechains: chain_data}
      }
    } = Tornex.SpecQuery.parse(active_warfare_query(), api_call_result)

    {_count, updated_chain_ids} = Tornium.Schema.Chain.upsert_all(chain_data)
    seen_chain_ids = Enum.uniq(updated_chain_ids ++ seen_chain_ids)

    paginate(chain_data, Kernel.length(chain_data), seen_chain_ids)
  end

  @spec paginate(
          chain_data :: [Torngen.Client.Schema.FactionChainWarfare.t()],
          number_chains :: non_neg_integer(),
          seen_chain_ids :: [pos_integer()]
        ) :: Oban.Worker.result()
  defp paginate(chain_data, number_chains, seen_chain_ids)
       when number_chains >= @api_query_limit and is_list(seen_chain_ids) do
    # If there is as much data as the limit, we want to paginate to the next page of chain
    # data. We can do this with the start timestamps of the chains as the meatadata links are
    # not entirely reliable.

    latest_start_timstamp =
      chain_data
      |> Enum.max_by(fn %Torngen.Client.Schema.FactionChainWarfare{values: chain_data_values} ->
        chain_data_values
        |> Enum.find(&match?(%Torngen.Client.Schema.FactionChain{}, &1))
        |> Map.get(:start)
      end)
      |> Map.get(:start)

    # Since the database can de-duplicate existing chains when it's upserting the data, we
    # should use the latest timestamp instead of the timstamp plus one to avoid losing
    # data on chains that start at the same time.
    schedule(from_timestamp: latest_start_timstamp, seen_chain_ids: seen_chain_ids)
  end

  defp paginate(_chain_data, _number_chains, seen_chain_ids) do
    # There are no more pages of chains to upsert into the database. Since we have sufficient
    # pages of chain data, we want to determine which chains were not updated as they are in
    # cooldown now. We should also update chain length when we're doing this.
    Tornium.Schema.Chain
    |> where([c], c.chain_id not in ^seen_chain_ids and is_nil(c.end_timestamp))
    |> select([c], {c.chain_id, c.faction_id})
    |> Repo.all()
    |> Enum.each(fn {chain_id, faction_id} -> Tornium.Workers.ChainUpdate.schedule(chain_id, faction_id) end)
  end

  @spec active_warfare_query(from_timestamp :: non_neg_integer()) :: Tornex.SpecQuery.t()
  defp active_warfare_query(from_timestamp \\ 0) when is_integer(from_timestamp) do
    # We want to quarntine this query to avoid causing issues with other queries as this doesn't
    # belong to any resource. This could also be potenially be done with a resource_id of 0 or
    # similar.
    Tornex.SpecQuery.new(nice: -10, quarantine?: true)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Warfarechains)
    |> Tornex.SpecQuery.put_parameter!(:cat, "active")
    |> Tornex.SpecQuery.put_parameter!(:limit, @api_query_limit)
    |> Tornex.SpecQuery.put_parameter!(:from, from_timestamp)
  end

  @spec schedule(opts :: keyword()) :: {:ok, Oban.Job.t()} | {:error, Oban.Job.changeset() | term()}
  defp schedule(opts \\ []) do
    from_timestamp = Keyword.get(opts, :from_timestamp, 0)
    seen_chain_ids = Keyword.get(opts, :seen_chain_ids, [])

    public_api_key = Tornium.User.Key.get_random!()
    api_call_id = Ecto.UUID.generate()
    Tornium.API.Store.create(api_call_id, @api_query_timeout)

    Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
      active_warfare_query(from_timestamp)
      |> Tornium.Schema.TornKey.put_key(public_api_key)
      |> Tornex.Scheduler.Bucket.enqueue(timeout: @api_query_timeout * 1_000)
      |> Tornium.API.Store.insert(api_call_id)
    end)

    %{api_call_id: api_call_id, user_id: public_api_key.user_id, seen_chain_ids: seen_chain_ids}
    |> new(schedule_in: _seconds = 5)
    |> Oban.insert()
  end
end
