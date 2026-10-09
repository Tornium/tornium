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

defmodule Tornium.Schema.Chain do
  @moduledoc """
  A chain for a faction.

  If the chain is not in cooldown yet, the chain `:end_timestamp` will be `nil` and the
  `:length` will be updated as the chain progresses.
  """

  use Ecto.Schema
  alias Tornium.Repo

  @type t :: %__MODULE__{
          chain_id: pos_integer(),
          faction_id: pos_integer(),
          faction: Tornium.Schema.Faction.t(),
          length: 0..100_000,
          start_timestamp: DateTime.t(),
          end_timestamp: DateTime.t() | nil
        }

  @minimum_chain_length 100
  @on_conflict_options [
    on_conflict: {:replace, [:length, :start_timestamp, :end_timestamp]},
    conflict_target: [:chain_id]
  ]

  @primary_key {:chain_id, :integer, autogenerate: false}
  schema "chain" do
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    field(:length, :integer)
    field(:start_timestamp, :utc_datetime)
    field(:end_timestamp, :utc_datetime)
  end

  # TODO: Document this
  @spec map(
          chain_data ::
            Torngen.Client.Schema.FactionChainWarfare.t()
            | Torngen.Client.Schema.FactionChainReport.t()
            | Torngen.Client.Schema.FactionChain.t(),
          faction_id :: pos_integer() | nil
        ) :: t()
  def map(chain_data, faction_id \\ nil)

  def map(%Torngen.Client.Schema.FactionChainWarfare{values: chain_data_values} = _chain_data, _faction_id) do
    %Torngen.Client.Schema.FactionChain{id: chain_id, chain: chain_length, start: chain_start_timestamp} =
      Enum.find(chain_data_values, &match?(%Torngen.Client.Schema.FactionChain{}, &1))

    %{faction: %{id: faction_id}} = Enum.find(chain_data_values, &match?(%{faction: %{id: _}}, &1))

    # The FactionChainWarfare struct would be provided from the active category of all
    # chains in the game. As such, we should set the timestamp for the end of the chain
    # to nil.
    %__MODULE__{
      chain_id: chain_id,
      faction_id: faction_id,
      length: chain_length,
      start_timestamp: chain_start_timestamp |> DateTime.from_unix!(:second),
      end_timestamp: nil
    }
  end

  def map(
        %Torngen.Client.Schema.FactionChainReport{
          id: chain_id,
          faction_id: faction_id,
          details: %Torngen.Client.Schema.FactionChainReportDetails{chain: chain_length},
          start: chain_start_timestamp,
          end: chain_end_timestamp
        } = _chain_data,
        _faction_id
      ) do
    %__MODULE__{
      chain_id: chain_id,
      faction_id: faction_id,
      length: chain_length,
      start_timestamp: chain_start_timestamp |> DateTime.from_unix!(:second),
      end_timestamp: chain_end_timestamp |> DateTime.from_unix!(:second)
    }
  end

  def map(
        %Torngen.Client.Schema.FactionChain{
          id: chain_id,
          chain: chain_length,
          start: chain_start_timestamp,
          end: chain_end_timestamp
        } = _chain_data,
        faction_id
      )
      when is_integer(faction_id) do
    %__MODULE__{
      chain_id: chain_id,
      faction_id: faction_id,
      length: chain_length,
      start_timestamp: chain_start_timestamp |> DateTime.from_unix!(:second),
      end_timestamp: chain_end_timestamp |> DateTime.from_unix!(:second)
    }
  end

  # TODO: document this
  @spec upsert(
          chain :: Torngen.Client.Schema.FactionChainReport.t() | Torngen.Client.Schema.FactionChain.t(),
          faction_id :: pos_integer()
        ) :: t() | nil
  def upsert(chain, faction_id) when is_integer(faction_id) do
    %__MODULE__{length: chain_length} = mapped_chain = map(chain, faction_id)

    if is_integer(chain_length) and chain_length >= @minimum_chain_length do
      Repo.insert!(mapped_chain, @on_conflict_options)
    else
      nil
    end
  end

  @doc """
  Upsert chains into the database.

  If a chain is below the `@minimum_chain_length`, the chain will not be inserted to conserve
  storage as to not store all the small chains.
  """
  @spec upsert_all(chains :: [Torngen.Client.Schema.FactionChainWarfare.t()]) ::
          {non_neg_integer(), [pos_integer()]}
  def upsert_all([%Torngen.Client.Schema.FactionChainWarfare{} | _] = chains) do
    chains
    |> Enum.map(fn %Torngen.Client.Schema.FactionChainWarfare{values: chain_data_values} ->
      %{faction: %{id: faction_id, name: faction_name}} =
        Enum.find(chain_data_values, &match?(%{faction: %{id: _}}, &1))

      {faction_id, faction_name}
    end)
    |> Tornium.Schema.Faction.ensure_exists()

    chains
    |> Enum.map(&map/1)
    |> Enum.reject(&(&1.length < @minimum_chain_length))
    |> upsert_all()
  end

  def upsert_all([%__MODULE__{} | _] = chains) do
    mapped_chains = Enum.map(chains, &to_map/1)
    upsert_opts = Keyword.merge(@on_conflict_options, returning: [:chain_id])
    {count, returned_chains} = Repo.insert_all(__MODULE__, mapped_chains, upsert_opts)

    {count, Enum.map(returned_chains, & &1.chain_id)}
  end

  def upsert_all([] = _chains) do
    {0, []}
  end

  @spec to_map(chain :: t()) :: map()
  defp to_map(
         %__MODULE__{
           chain_id: chain_id,
           faction_id: faction_id,
           length: length,
           start_timestamp: start_timestamp,
           end_timestamp: end_timestamp
         } = _chain
       ) do
    %{
      chain_id: chain_id,
      faction_id: faction_id,
      length: length,
      start_timestamp: start_timestamp,
      end_timestamp: end_timestamp
    }
  end
end
