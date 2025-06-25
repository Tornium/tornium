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

defmodule Tornium.Test.Faction.OC.Team.Check.Struct do
  use Tornium.RepoCase, async: true
  alias Tornium.Faction.OC.Team.Check
  alias Tornium.Schema.{OrganizedCrime, OrganizedCrimeTeam}

  test "test_no_assigns" do
    %Check.Struct{team_spawn_required: team_spawn_required, assigned_team: assigned_team} =
      Check.Struct.set_assigned_teams(%{})

    assert Enum.empty?(team_spawn_required)
    assert Enum.empty?(assigned_team)
  end

  test "test_assigned_teams" do
    %Check.Struct{team_spawn_required: team_spawn_required, assigned_team: assigned_team} =
      Check.Struct.set_assigned_teams(%{
        %OrganizedCrimeTeam{oc_name: "OC test 1"} => %OrganizedCrime{oc_name: "OC test 1"}
      })
      |> Check.Struct.set_assigned_teams(%{
        %OrganizedCrimeTeam{oc_name: "OC test 2"} => %OrganizedCrime{oc_name: "OC test 2"}
      })

    assert length(assigned_team) == 2
    assert Enum.empty?(team_spawn_required)

    assert assigned_team |> Enum.at(0) |> elem(0) |> Map.fetch!(:oc_name) == "OC test 2"
    assert assigned_team |> Enum.at(1) |> elem(0) |> Map.fetch!(:oc_name) == "OC test 1"
  end

  test "test_spawn_required" do
    %Check.Struct{team_spawn_required: team_spawn_required, assigned_team: assigned_team} =
      Check.Struct.set_assigned_teams(%{
        %OrganizedCrimeTeam{oc_name: "OC test 1"} => %OrganizedCrime{oc_name: "OC test 1"},
        %OrganizedCrimeTeam{oc_name: "OC test 2"} => {:spawn_required, "OC test 2"},
        %OrganizedCrimeTeam{oc_name: "OC test 3"} => {:spawn_required, "OC test 3"}
      })

    assert length(assigned_team) == 1
    assert length(team_spawn_required) == 2

    assert team_spawn_required |> Enum.at(0) |> Map.fetch!(:oc_name) == "OC test 3"
    assert team_spawn_required |> Enum.at(1) |> Map.fetch!(:oc_name) == "OC test 2"
  end

  test "test_spawn_required_skipped" do
    # If an OC has had a notification sent within 24 hours, there will not be a notification sent
    %Check.Struct{team_spawn_required: team_spawn_required, assigned_team: assigned_team} =
      Check.Struct.set_assigned_teams(%{
        %OrganizedCrimeTeam{oc_name: "OC test 1"} => %OrganizedCrime{oc_name: "OC test 1"},
        %OrganizedCrimeTeam{oc_name: "OC test 2"} => {:spawn_required, "OC test 2"},
        %OrganizedCrimeTeam{oc_name: "OC test 3", required_spawn_at: nil} => {:spawn_required, "OC test 3"},
        %OrganizedCrimeTeam{oc_name: "OC test 4", required_spawn_at: DateTime.utc_now() |> DateTime.add(-23, :hour)} =>
          {:spawn_required, "OC test 4"},
        %OrganizedCrimeTeam{oc_name: "OC test 5", required_spawn_at: DateTime.utc_now() |> DateTime.add(-48, :hour)} =>
          {:spawn_required, "OC test 5"}
      })

    assert length(assigned_team) == 1
    assert length(team_spawn_required) == 3

    assert team_spawn_required |> Enum.at(0) |> Map.fetch!(:oc_name) == "OC test 5"
    assert team_spawn_required |> Enum.at(1) |> Map.fetch!(:oc_name) == "OC test 3"
    assert team_spawn_required |> Enum.at(2) |> Map.fetch!(:oc_name) == "OC test 2"
  end
end
