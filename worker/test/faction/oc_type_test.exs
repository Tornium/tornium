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

defmodule Tornium.Test.Faction.OrganizedCrimeType do
  use Tornium.RepoCase, async: true

  alias Tornium.Schema.{OrganizedCrimeType, OrganizedCrimeSlotType}
  alias Torngen.Client.Schema.{TornOrganizedCrime, TornOrganizedCrimeSpawn, TornOrganizedCrimeSlot}

  doctest Tornium.Schema.OrganizedCrimeType, only: [{:map_spawn_level!, 1}], import: true

  test "validate parsing" do
    crime_type =
      OrganizedCrimeType.from_data!(%TornOrganizedCrime{
        name: "Test",
        description: "This is a test",
        difficulty: 10,
        spawn: %TornOrganizedCrimeSpawn{level: 2},
        slots: []
      })

    assert crime_type.name == "Test"
    assert crime_type.description == "This is a test"
    assert crime_type.difficulty == 10
    assert crime_type.spawn_level == :sigma
  end
end
