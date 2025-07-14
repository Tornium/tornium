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

  test "check_incorrect_member_unassigned" do
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
    # TODO: Implement this test
  end

  test "check_incorrect_member_invalid" do
    # TODO: Implement this test
  end
end
