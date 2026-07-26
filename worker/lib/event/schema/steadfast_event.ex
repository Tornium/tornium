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

defmodule Tornium.Schema.SteadfastEvent do
  @moduledoc """
  A steadfast rotation for one/two stats in a faction.
  """

  use Ecto.Schema

  @typedoc """
  The steadfast of a stat in a faction.
  """
  @type steadfast() :: 0..20

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          faction_id: pos_integer(),
          faction: Tornium.Schema.Faction.t(),
          strength: steadfast(),
          defense: steadfast(),
          speed: steadfast(),
          dexterity: steadfast(),
          start_timestamp: DateTime.t(),
          end_timestamp: DateTime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "steadfast_event" do
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    field(:strength, :integer)
    field(:defense, :integer)
    field(:speed, :integer)
    field(:dexterity, :integer)

    field(:start_timestamp, :utc_datetime)
    field(:end_timestamp, :utc_datetime)
  end
end
