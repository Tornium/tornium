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

defmodule Tornium.Schema.FactionPosition do
  @moduledoc """
  Schema for each of the faction positions of a faction.
  """

  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          pid: Ecto.UUID.t(),
          name: String.t(),
          faction_id: pos_integer(),
          faction: Tornium.Schema.Faction.t(),
          default: boolean(),
          permissions: [Torngen.Client.Schema.FactionPositionAbilityEnum.t()]
        }

  @primary_key {:pid, Ecto.UUID, autogenerate: true}
  schema "faction_position" do
    field(:name, :string)
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    field(:default, :boolean)
    field(:permissions, {:array, :string})
  end

  @doc """
  Map the faction position data for a specfic position to a `Tornium.Schema.FactionPosition`.
  """
  @spec map(position_data :: Torngen.Client.Schema.FactionPosition.t(), faction_id :: pos_integer()) :: t()
  def map(
        %Torngen.Client.Schema.FactionPosition{
          name: position_name,
          is_default: position_default?,
          abilities: position_abilities
        } = _position_data,
        faction_id
      )
      when is_binary(position_name) and is_binary(position_default?) and is_list(position_abilities) and
             is_integer(faction_id) do
    %__MODULE__{
      pid: Ecto.UUID.generate(),
      name: position_name,
      faction_id: faction_id,
      default: position_default?,
      permissions: position_abilities
    }
  end

  @doc """
  Upsert faction positions for a faction ID into the database.
  """
  @spec upsert_all(positions :: [t() | Torngen.Client.Schema.FactionPosition.t()], faction_id :: pos_integer()) :: [t()]
  def upsert_all([%Torngen.Client.Schema.FactionPosition{} | _] = positions, faction_id) when is_integer(faction_id) do
    positions
    |> Enum.map(&map(&1, faction_id))
    |> upsert_all(faction_id)
  end

  def upsert_all([%__MODULE__{} | _] = positions, _faction_id) do
    map_positions =
      Enum.map(
        positions,
        &%{
          pid: &1.pid,
          name: &1.name,
          faction_id: &1.faction_id,
          default: &1.default,
          permissions: &1.permissions
        }
      )

    {_count, upserted_positions} =
      Repo.insert_all(__MODULE__, map_positions,
        on_conflict: {:replace, [:name, :default, :permissions]},
        conflict_target: [:pid],
        returning: true
      )

    upserted_positions
  end

  def upsert_all([], _faction_id) do
    []
  end

  @doc """
  Remove the old faction positions from members and delete those faction positions.
  """
  @spec remove_old_positions(current_positions :: [t()], faction_id :: pos_integer()) :: term()
  def remove_old_positions(current_positions, faction_id) when is_list(current_positions) and is_integer(faction_id) do
    # TODO: Test this
    current_position_names = Enum.map(current_positions, & &1.name)

    old_position_ids =
      Tornium.Schema.FactionPosition
      |> select([p], p.pid)
      |> where([p], p.name not in ^current_position_names and p.faction_id == ^faction_id)
      |> Repo.all()

    Tornium.Schema.User
    |> where([u], u.faction_position_id in ^old_position_ids)
    |> Repo.update_all(set: [faction_aa: false, faction_position_id: nil])

    Tornium.Schema.FactionPosition
    |> where([p], p.pid in ^old_position_ids)
    |> Repo.delete_all()
  end
end
