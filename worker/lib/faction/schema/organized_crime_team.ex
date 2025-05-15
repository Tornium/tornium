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

defmodule Tornium.Schema.OrganizedCrimeTeam do
  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          name: String.t(),
          members: [Tornium.Schema.OrganizedCrimeTeamMember.t()],
          crimes: [Tornium.Schema.OrganizedCrime.t()],
          current_crime: Tornium.Schema.OrganizedCrime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_team" do
    field(:name, :string)

    has_many(:members, Tornium.Schema.OrganizedCrimeTeamMember, foreign_key: :guid)
    has_many(:crimes, Tornium.Schema.OrganizedCrime, foreign_key: :assigned_team_id)
    has_one(:current_crime, Tornium.Schema.OrganizedCrime, foreign_key: :assigned_team_id)
  end
end
