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

defmodule Tornium.Schema.OrganizedCrimeSlotType do
  @moduledoc """
  Data on each slot of an organized crime.

  Each slot is represented as a combination of its name, number, and index. The name of the
  slot is just the name of the position. The number of the slot is `1` if there is only one
  slot of tht position name and is the number of the position name if there is more than
  one. For example, for `Muscle #2`, the name is `Muscle` and the number is `2`. The index
  of the slot is the overall index of the OC amongst all of the slots.

  NOTE: The index uses one-indexing.
  """

  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          oc_type_id: Ecto.UUID.t(),
          oc_type: Tornium.Schema.OrganizedCrimeType.t(),
          name: String.t(),
          number: pos_integer(),
          index: pos_integer(),
          required_item_id: pos_integer() | nil,
          required_item: Tornium.Schema.Item.t() | nil,
          required_item_consumed: boolean() | nil
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_slot_type" do
    belongs_to(:oc_type, Tornium.Schema.OrganizedCrimeType, references: :guid, type: Ecto.UUID)

    field(:name, :string)
    field(:number, :integer)
    field(:index, :integer)

    belongs_to(:required_item, Tornium.Schema.Item, references: :tid)
    field(:required_item_consumed, :boolean)
  end

  # TODO: Add doc
  @spec from_data!(data :: Torngen.Client.Schema.TornOrganizedCrimeSlot.t(), oc_type_id :: Ecto.UUID.t()) :: t()
  def from_data!(
        %Torngen.Client.Schema.TornOrganizedCrimeSlot{
          name: position_name,
          position_info: %Torngen.Client.Schema.FactionSlotPositionInfo{
            id: "P" <> position_index,
            number: position_number
          },
          required_item: %Torngen.Client.Schema.TornOrganizedCrimeRequiredItem{
            id: required_item_id,
            is_used: required_item_consumed?
          }
        } = _data,
        oc_type_id
      ) do
    %__MODULE__{
      guid: Ecto.UUID.generate(),
      oc_type_id: oc_type_id,
      name: position_name,
      number: position_number,
      index: String.to_integer(position_index),
      required_item_id: required_item_id,
      required_item_consumed: required_item_consumed?
    }
  end

  def from_data!(
        %Torngen.Client.Schema.TornOrganizedCrimeSlot{
          name: position_name,
          position_info: %Torngen.Client.Schema.FactionSlotPositionInfo{
            id: "P" <> position_index,
            number: position_number
          },
          required_item: nil
        } = _data,
        oc_type_id
      ) do
    %__MODULE__{
      guid: Ecto.UUID.generate(),
      oc_type_id: oc_type_id,
      name: position_name,
      number: position_number,
      index: String.to_integer(position_index),
      required_item_id: nil,
      required_item_consumed: nil
    }
  end

  # TODO: Add doc
  # TEST: Add test
  @spec upsert_all!(
          data :: Torngen.Client.Schema.TornOrganizedCrimeResponse.t(),
          crime_types :: [Tornium.Schema.OrganizedCrimeType.t()]
        ) :: :ok
  def upsert_all!(%Torngen.Client.Schema.TornOrganizedCrimeResponse{organizedcrimes: crimes} = _data, crime_types)
      when is_list(crime_types) do
    slot_type_entries =
      crimes
      |> Enum.flat_map(fn %Torngen.Client.Schema.TornOrganizedCrime{name: oc_type_name, slots: slots} ->
        %Tornium.Schema.OrganizedCrimeType{guid: oc_type_guid} =
          Enum.find(crime_types, &(&1.name == oc_type_name))

        Enum.map(slots, fn slot ->
          slot
          |> from_data!(oc_type_guid)
          |> Map.from_struct()
          |> Map.drop([:__struct__, :__meta__, :oc_type, :required_item])
        end)
      end)

    Repo.insert_all(__MODULE__, slot_type_entries,
      conflict_target: [:oc_type_id, :index],
      on_conflict: {:replace, [:name, :number, :required_item_id, :required_item_consumed]}
    )

    :ok
  end

  @doc """
  Get the slot type from the OC name, the slot slot, and the slot number.

  If the data comes from an `Tornium.Schema.OrganizedCrimeSlot`, the `slot_number` paramter
  of this function corresponds to `OrganizedCrimeSlot.crime_position_index`.
  """
  @spec get(oc_name :: String.t(), slot_name :: String, slot_number :: pos_integer()) :: t() | nil
  def get(oc_name, slot_name, slot_number)
      when is_binary(oc_name) and is_binary(slot_name) and is_integer(slot_number) do
    __MODULE__
    |> where([s], s.name == ^slot_name and s.number == ^slot_number)
    |> join(:inner, [s], c in assoc(s, :oc_type), on: s.oc_type_id == c.guid)
    |> where([s, c], c.name == ^oc_name)
    |> preload(:oc_type)
    |> Repo.one()
  end
end
