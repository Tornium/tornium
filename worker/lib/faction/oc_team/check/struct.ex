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

defmodule Tornium.Faction.OC.Team.Check.Struct do
  @moduledoc """
  Struct containing triggered checks related to organized crime teams.
  """

  defstruct [:team_spawn_required, :assigned_team]

  @type t :: %Tornium.Faction.OC.Team.Check.Struct{
          team_spawn_required: [Tornium.Schema.OrganizedCrimeTeam.t()],
          assigned_team: [{Tornium.Schema.OrganizedCrimeTeam.t(), Tornium.Schema.OrganizedCrime.t()}]
        }
  @type keys :: :team_spawn_required | :assigned_team

  @doc """
  Create a new OC Team check struct.

  This struct will handle and store triggered checks related to OC teams and their assigned OCs.
  """
  @spec new() :: t()
  def new() do
    %Tornium.Faction.OC.Team.Check.Struct{
      team_spawn_required: [],
      assigned_team: []
    }
  end

  @doc """
  Update the check struct provided the new organized crime team assignments.

  If the check struct has not been passed, a new `Tornium.Faction.OC.Team.Check.Struct` will be
  created. If the OC team requires an OC to be spawned and that requirement has been 
  "registered" within the last 24 hours, the spawning requirement will not be added to the check 
  struct to avoid sending a message every time the OC team checks are run.
  """
  @spec set_assigned_teams(assignments :: Tornium.Faction.OC.Team.new_team_assignments()) :: t()
  def set_assigned_teams(assignments) do
    set_assigned_teams(new(), assignments)
  end

  @spec set_assigned_teams(check_struct :: t(), assignments :: Tornium.Faction.OC.Team.new_team_assignments()) :: t()
  def set_assigned_teams(%__MODULE__{} = check_struct, assignments) do
    # TODO: Test this
    Enum.reduce(assignments, check_struct, &do_set_assigned_teams/2)
  end

  @spec do_set_assigned_teams(
          {team :: Tornium.Schema.OrganizedCrimeTeam.t(), crime :: Tornium.Schema.OrganizedCrime.t()}
          | {:spawn_required, oc_name :: String.t()},
          acc :: t()
        ) :: t()
  defp do_set_assigned_teams(
         {%Tornium.Schema.OrganizedCrimeTeam{} = team, %Tornium.Schema.OrganizedCrime{} = crime},
         %__MODULE__{assigned_team: assigned_team} = acc
       ) do
    %__MODULE__{acc | assigned_team: [{team, crime} | assigned_team]}
  end

  defp do_set_assigned_teams(
         {%Tornium.Schema.OrganizedCrimeTeam{required_spawn_at: required_spawn_at} = team, {:spawn_required, _oc_name}},
         %__MODULE__{team_spawn_required: team_spawn_required} = acc
       ) do
    if is_nil(required_spawn_at) or DateTime.diff(DateTime.utc_now(), required_spawn_at, :hour) >= 24 do
      %__MODULE__{acc | team_spawn_required: [team | team_spawn_required]}
    else
      acc
    end
  end
end
