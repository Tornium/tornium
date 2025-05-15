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

defmodule Tornium.Schema.OrganizedCrimeTeamMember do
  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          user_id: integer(),
          user: Tornium.Schema.User.t(),
          team_id: Ecto.UUID.t(),
          team: Tornium.Schema.OrganizedCrimeTeam.t(),
          slot_type: String.t(),
          slot_index: integer()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_team_member" do
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    belongs_to(:team, Tornium.Schema.OrganizedCrimeTeam, references: :guid)

    field(:slot_type, :string)
    field(:slot_index, :integer)
  end
end
