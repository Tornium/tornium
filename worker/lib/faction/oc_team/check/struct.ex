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
  # TODO: Add moduledoc

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

  # TODO: Add documentation
  @doc """
  """
  @spec set_assigned_teams(assignments :: Tornium.Faction.OC.Team.new_team_assignments()) :: t()
  def set_assigned_teams(assignments) do
    set_assigned_teams(new(), assignments)
  end

  @spec set_assigned_teams(check_struct :: t(), assignments :: Tornium.Faction.OC.Team.new_team_assignments()) :: t()
  def set_assigned_teams(%__MODULE__{} = check_struct, assignments) do
    Enum.reduce(assignments, check_struct, &do_set_assigned_teams/2)
  end

  defp do_set_assigned_teams(
         {%Tornium.Schema.OrganizedCrimeTeam{} = team, %Tornium.Schema.OrganizedCrime{} = crime},
         %__MODULE__{assigned_team: assigned_team} = acc
       ) do
    %__MODULE__{acc | assigned_team: [{team, crime} | assigned_team]}
  end

  defp do_set_assigned_teams(
         {%Tornium.Schema.OrganizedCrimeTeam{} = team, {:spawn_required, _oc_name}},
         %__MODULE__{team_spawn_required: team_spawn_required} = acc
       ) do
    %__MODULE__{acc | team_spawn_required: [team | team_spawn_required]}
  end
end
