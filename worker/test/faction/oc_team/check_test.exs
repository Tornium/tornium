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

defmodule Tornium.Test.Faction.OC.Team.Check do
  use Tornium.RepoCase, async: true

  doctest Tornium.Faction.OC.Team.Check, only: [{:member_in_crime?, 2}]

  test "check_member_join_required_all_joined" do
    team = %Tornium.Schema.OrganizedCrimeTeam{
      members: [
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 2}
      ],
      current_crime: %Tornium.Schema.OrganizedCrime{
        slots: [
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 2},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 1}
        ]
      }
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_member_join_required(team)

    assert Enum.empty?(check_struct.team_member_join_required)
  end

  test "check_member_join_required_wildcard_member" do
    team = %Tornium.Schema.OrganizedCrimeTeam{
      members: [
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: nil},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: nil}
      ],
      current_crime: %Tornium.Schema.OrganizedCrime{
        slots: [
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 2},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: nil}
        ]
      }
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_member_join_required(team)

    assert Enum.empty?(check_struct.team_member_join_required)
  end

  test "check_member_join_required_missing_member" do
    team = %Tornium.Schema.OrganizedCrimeTeam{
      members: [
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 2}
      ],
      current_crime: %Tornium.Schema.OrganizedCrime{
        slots: [
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 2},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 3}
        ]
      }
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_member_join_required(team)

    assert length(check_struct.team_member_join_required) == 1

    {member, crime} = Enum.at(check_struct.team_member_join_required, 0)
    assert member.user_id == 1
    assert not is_nil(crime)
  end

  test "find_incorrect_crime_valid" do
    crimes = [
      %Tornium.Schema.OrganizedCrime{
        assigned_team_id: 1,
        slots: [%Tornium.Schema.OrganizedCrimeSlot{user_id: 1}, %Tornium.Schema.OrganizedCrimeSlot{user_id: 2}]
      }
    ]

    incorrect_crime =
      Tornium.Faction.OC.Team.Check.find_incorrect_crime(
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1, team_id: 1},
        crimes
      )

    assert is_nil(incorrect_crime)
  end

  test "find_incorrect_crime_invalid" do
    crimes = [
      %Tornium.Schema.OrganizedCrime{
        assigned_team_id: 1,
        slots: [%Tornium.Schema.OrganizedCrimeSlot{user_id: 1}, %Tornium.Schema.OrganizedCrimeSlot{user_id: 2}]
      },
      %Tornium.Schema.OrganizedCrime{
        assigned_team_id: 2,
        slots: [%Tornium.Schema.OrganizedCrimeSlot{user_id: 3}, %Tornium.Schema.OrganizedCrimeSlot{user_id: 4}]
      }
    ]

    incorrect_crime =
      Tornium.Faction.OC.Team.Check.find_incorrect_crime(
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1, team_id: 2},
        crimes
      )

    assert not is_nil(incorrect_crime)
    assert incorrect_crime.assigned_team_id == 1
    assert Enum.at(incorrect_crime.slots, 0).user_id == 1
  end

  test "check_incorrect_member_wildcard" do
    team = %Tornium.Schema.OrganizedCrimeTeam{
      current_crime: nil,
      members: []
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_incorrect_member(team)

    assert Enum.empty?(check_struct.team_incorrect_member)
  end

  test "check_incorrect_member_valid" do
    team = %Tornium.Schema.OrganizedCrimeTeam{
      current_crime: %Tornium.Schema.OrganizedCrime{
        slots: [
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 1, crime_position: "Muscle", crime_position_index: 1},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 2, crime_position: "Muscle", crime_position_index: 2},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 3, crime_position: "Pickpocket", crime_position_index: 1}
        ]
      },
      members: [
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 2, slot_type: "Muscle", slot_index: 2},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 3, slot_type: "Pickpocket", slot_index: 1},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1, slot_type: "Muscle", slot_index: 1}
      ]
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_incorrect_member(team)

    assert Enum.empty?(check_struct.team_incorrect_member)
  end

  test "check_incorrect_member_invalid" do
    team = %Tornium.Schema.OrganizedCrimeTeam{
      current_crime: %Tornium.Schema.OrganizedCrime{
        oc_name: "foo",
        slots: [
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 1, crime_position: "Muscle", crime_position_index: 1},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 2, crime_position: "Muscle", crime_position_index: 2},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 4, crime_position: "Pickpocket", crime_position_index: 1}
        ]
      },
      members: [
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1, slot_type: "Muscle", slot_index: 2},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 3, slot_type: "Pickpocket", slot_index: 1},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 2, slot_type: "Muscle", slot_index: 1}
      ]
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_incorrect_member(team)

    assert length(check_struct.team_incorrect_member) == 1

    {
      %Tornium.Schema.OrganizedCrimeSlot{
        user_id: incorrect_slot_user_id,
        crime_position: crime_position,
        crime_position_index: crime_position_index
      },
      %Tornium.Schema.OrganizedCrime{oc_name: oc_name}
    } = Enum.at(check_struct.team_incorrect_member, 0)

    assert oc_name == "foo"
    assert incorrect_slot_user_id == 4
    assert crime_position == "Pickpocket"
    assert crime_position_index == 1
  end

  test "check_incorrect_slot_wildcard" do
    team = %Tornium.Schema.OrganizedCrimeTeam{
      current_crime: %Tornium.Schema.OrganizedCrime{
        slots: [%Tornium.Schema.OrganizedCrimeSlot{user_id: 1, crime_position: "Muscle", crime_position_index: 1}]
      },
      members: [%Tornium.Schema.OrganizedCrimeTeamMember{user_id: nil, slot_type: "Muscle", slot_index: 1}]
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_member_incorrect_slot(team)

    assert Enum.empty?(check_struct.team_member_incorrect_slot)
  end

  test "check_incorrect_slot_valid" do
    team = %Tornium.Schema.OrganizedCrimeTeam{
      current_crime: %Tornium.Schema.OrganizedCrime{
        slots: [
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 1, crime_position: "Muscle", crime_position_index: 1},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 2, crime_position: "Muscle", crime_position_index: 2},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 3, crime_position: "Muscle", crime_position_index: 3},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 4, crime_position: "Pickpocket", crime_position_index: 1},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 5, crime_position: "Thief", crime_position_index: 1}
        ]
      },
      members: [
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 3, slot_type: "Muscle", slot_index: 3},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 5, slot_type: "Thief", slot_index: 1},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 4, slot_type: "Pickpocket", slot_index: 1},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 2, slot_type: "Muscle", slot_index: 2},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1, slot_type: "Muscle", slot_index: 1}
      ]
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_member_incorrect_slot(team)

    assert Enum.empty?(check_struct.team_member_incorrect_slot)
  end

  test "check_incorrect_slot_invalid" do
    # OC team member is in wrong slot of the OC
    team = %Tornium.Schema.OrganizedCrimeTeam{
      current_crime: %Tornium.Schema.OrganizedCrime{
        slots: [
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 3, crime_position: "Muscle", crime_position_index: 1},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 2, crime_position: "Muscle", crime_position_index: 2},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 1, crime_position: "Muscle", crime_position_index: 3}
        ]
      },
      members: [
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 3, slot_type: "Muscle", slot_index: 3},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 2, slot_type: "Muscle", slot_index: 2},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1, slot_type: "Muscle", slot_index: 1}
      ]
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_member_incorrect_slot(team)

    assert length(check_struct.team_member_incorrect_slot) == 2

    assert Enum.any?(check_struct.team_member_incorrect_slot, fn {team_member, slot} ->
             slot.user_id == 3 and team_member.user_id == 1 and team_member.slot_index == 1
           end)

    assert Enum.any?(check_struct.team_member_incorrect_slot, fn {team_member, slot} ->
             slot.user_id == 1 and team_member.user_id == 3 and team_member.slot_index == 3
           end)
  end

  test "check_invalid_slot_incorrect_member" do
    # Slot held by user that is not an OC team member is invalid
    team = %Tornium.Schema.OrganizedCrimeTeam{
      current_crime: %Tornium.Schema.OrganizedCrime{
        slots: [
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 1, crime_position: "Muscle", crime_position_index: 1},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 2, crime_position: "Muscle", crime_position_index: 2},
          %Tornium.Schema.OrganizedCrimeSlot{user_id: 4, crime_position: "Muscle", crime_position_index: 3}
        ]
      },
      members: [
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 3, slot_type: "Muscle", slot_index: 3},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 2, slot_type: "Muscle", slot_index: 2},
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1, slot_type: "Muscle", slot_index: 1}
      ]
    }

    check_struct =
      Tornium.Faction.OC.Team.Check.Struct.new()
      |> Tornium.Faction.OC.Team.Check.check_member_incorrect_slot(team)

    assert Enum.empty?(check_struct.team_member_incorrect_slot)
  end
end
