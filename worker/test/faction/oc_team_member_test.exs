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

defmodule Tornium.Test.Schema.OrganizedCrimeTeamMember do
  use Tornium.RepoCase, async: true
  alias Tornium.Schema.OrganizedCrimeTeamMember

  doctest Tornium.Schema.OrganizedCrimeTeamMember, only: [{:wildcard?, 1}]

  test "test_find_members" do
    members = [
      %OrganizedCrimeTeamMember{user_id: 1, slot_type: "Muscle", slot_index: 0, slot_count: 0},
      %OrganizedCrimeTeamMember{user_id: 2, slot_type: "Muscle", slot_index: 1, slot_count: 1},
      %OrganizedCrimeTeamMember{user_id: 3, slot_type: "Muscle", slot_index: 2, slot_count: 2},
      %OrganizedCrimeTeamMember{user_id: 4, slot_type: "Robber", slot_index: 0, slot_count: 3},
      %OrganizedCrimeTeamMember{user_id: 5, slot_type: "Thief", slot_index: 0, slot_count: 4},
      %OrganizedCrimeTeamMember{user_id: 6, slot_type: "Thief", slot_index: 1, slot_count: 5}
    ]

    robber = OrganizedCrimeTeamMember.find_slot_member(members, "Robber", 0)
    muscle_two = OrganizedCrimeTeamMember.find_slot_member(members, "Muscle", 1)
    muscle_three = OrganizedCrimeTeamMember.find_slot_member(members, "Muscle", 2)
    invalid_member = OrganizedCrimeTeamMember.find_slot_member(members, "FooBar", 1)

    assert not is_nil(robber)
    assert robber.user_id == 4
    assert robber.slot_count == 3

    assert not is_nil(muscle_two)
    assert muscle_two.user_id == 2
    assert muscle_two.slot_count == 1

    assert not is_nil(muscle_three)
    assert muscle_three.user_id == 3
    assert muscle_three.slot_count == 2

    assert is_nil(invalid_member)
  end
end
