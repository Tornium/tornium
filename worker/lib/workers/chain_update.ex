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

defmodule Tornium.Workers.ChainUpdate do
  @moduledoc """
  Update a specific chain of a faction.
  """

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction"]

  @api_query_timeout 300

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args:
            %{
              "api_call_id" => api_call_id,
              "chain_id" => chain_id,
              "faction_id" => faction_id
            } = _args
        } = _job
      ) do
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
        do_perform(result, chain_id, faction_id)
    end
  end

  @spec do_perform(api_call_result :: term(), chain_id :: pos_integer(), faction_id :: pos_integer()) ::
          Oban.Worker.result()
  defp do_perform(%{"chainreport" => _} = api_call_result, chain_id, faction_id)
       when is_integer(chain_id) and is_integer(faction_id) do
    # If there's a chainreport key in the resulting API response, this indicates that there was
    # an AA API key available as the faction/<chain_id>/chainreport endpoint requires the API key
    # of a member and we'll fallback to the faction/<id>/chains endpoint if that is not available.
    base_query = query(chain_id, faction_id, true)

    %{
      Torngen.Client.Path.Faction.ChainId.Chainreport => %{
        FactionChainReportResponse => %Torngen.Client.Schema.FactionChainReportResponse{
          chainreport: %Torngen.Client.Schema.FactionChainReport{id: ^chain_id} = chain_report
        }
      }
    } = Tornex.SpecQuery.parse(base_query, api_call_result)

    chain_report
    |> Tornium.Schema.Chain.upsert(faction_id)

    :ok
  end

  defp do_perform(%{"chains" => _} = api_call_result, chain_id, faction_id)
       when is_integer(chain_id) and is_integer(faction_id) do
    # If there's a chains key in the resulting API response, this indicates that there was no AA
    # API key available and we'll fallback to the faction/<id>/chains endpoint if that is not
    # available.
    base_query = query(chain_id, faction_id, false)

    %{
      Torngen.Client.Path.Faction.Id.Chains => %{
        FactionChainsResponse => %Torngen.Client.Schema.FactionChainsResponse{
          chains: chains
        }
      }
    } = Tornex.SpecQuery.parse(base_query, api_call_result)

    chains
    |> Enum.find(&(&1.id == chain_id))
    |> Tornium.Schema.Chain.upsert(faction_id)

    :ok
  end

  @doc """
  Schedule the Oban Job to update a specific chain in the database.

  If there is an AA API key, a chain report will be used to fetch the chain data, otherwise
  we will use a public API key to fetch the minimal chain data for the chain.
  """
  @spec schedule(chain_id :: pos_integer(), faction_id :: pos_integer()) ::
          {:ok, Oban.Job.t()} | {:error, Oban.Job.changeset() | term()}
  def schedule(chain_id, faction_id) when is_integer(chain_id) and is_integer(faction_id) do
    # The faction/<chain_id>/chainreport endpoint requires a public API key of a member of that
    # faction. If there is no AA API key, we can use the faction/<id>/chains endpoint. This allows
    # chain reports to compiled in the future.
    {api_key, faction_key_available?} =
      case Tornium.Faction.get_key(faction_id) do
        %Tornium.Schema.TornKey{} = api_key ->
          {api_key, true}

        nil ->
          {Tornium.User.Key.get_random!(), false}
      end

    api_call_id = Ecto.UUID.generate()
    Tornium.API.Store.create(api_call_id, @api_query_timeout)

    Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
      query(chain_id, faction_id, faction_key_available?)
      |> Tornium.Schema.TornKey.put_key(api_key)
      |> Tornex.Scheduler.Bucket.enqueue(timeout: @api_query_timeout * 1_000)
      |> Tornium.API.Store.insert(api_call_id)
    end)

    %{api_call_id: api_call_id, faction_id: faction_id, chain_id: chain_id, user_id: api_key.user_id}
    |> new(schedule_in: _seconds = 15)
    |> Oban.insert()
  end

  @spec query(chain_id :: pos_integer(), faction_id :: pos_integer(), faction_key_available? :: boolean()) ::
          Tornex.SpecQuery.t()
  defp query(chain_id, faction_id, true = _faction_key_available?)
       when is_integer(chain_id) and is_integer(faction_id) do
    Tornex.SpecQuery.new()
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.ChainId.Chainreport)
    |> Tornex.SpecQuery.put_parameter!(:chainId, chain_id)
  end

  defp query(chain_id, faction_id, false = _faction_key_available?)
       when is_integer(chain_id) and is_integer(faction_id) do
    Tornex.SpecQuery.new()
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Chains)
    |> Tornex.SpecQuery.put_parameter!(:id, faction_id)
  end
end
