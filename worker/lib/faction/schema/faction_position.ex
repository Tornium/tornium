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
end
