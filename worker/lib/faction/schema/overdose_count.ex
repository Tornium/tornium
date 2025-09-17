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

defmodule Tornium.Schema.OverdoseCount do
  @moduledoc """
  Schema for overdose counts for members of a faction.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          faction_id: integer(),
          faction: Tornium.Schema.Faction.t(),
          user_id: integer(),
          user: Tornium.Schema.User.t(),
          count: integer(),
          updated_at: DateTime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "overdose_event" do
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    belongs_to(:user, Tornium.Schema.User, references: :tid)

    field(:count, :integer)
    field(:updated_at, :utc_datetime)
  end
end
