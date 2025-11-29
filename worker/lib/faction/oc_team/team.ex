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

defmodule Tornium.Faction.OC.Team do
  @moduledoc """
  Functionality related to organized crime teams.
  """

  @type new_team_assignments :: %{
          Tornium.Schema.OrganizedCrimeTeam.t() => Tornium.Schema.OrganizedCrime.t() | {:spawn_required, String.t()}
        }

  @doc """
  Assign organized crimes to organized crime teams.

  Organized crime teams that have completed their OC (or have an expired OC) or are recently created and don't have an 
  assigned OC will be assigned a new organized crime. If there is an available OC of the correct OC name, the OC team 
  will be assigned to that OC. If there does not exist such an OC, the `{:spawn_required, oc_name}` will be returned
  for the OC team to indicate that an OC manager will need to spawn an OC of that name.

  It is assumed that the provided OC teams are already filtered to not include teams of completed OCs, teams of
  expired OCs, and new OC teams. While assigning OCs to teams, priority will be given to an OC partially filled with
  exclusively members of a team.
  """
  @spec reassign_teams(
          teams :: [Tornium.Schema.OrganizedCrimeTeam.t()],
          crimes :: [Tornium.Schema.OrganizedCrime.t()],
          assignments :: new_team_assignments()
        ) :: new_team_assignments()
  def reassign_teams(teams, crimes, assignments \\ %{})

  def reassign_teams(
        [%Tornium.Schema.OrganizedCrimeTeam{} = team | remaining_teams] = _teams,
        [%Tornium.Schema.OrganizedCrime{} | _remaining_crimes] = crimes,
        assignments
      )
      when is_map(assignments) do
    {crimes, assignments} =
      team
      |> filter_team_crimes(crimes)
      |> List.first()
      |> do_assign_team(crimes, team, assignments)

    reassign_teams(remaining_teams, crimes, assignments)
  end

  def reassign_teams(_teams, [] = _crimes, assignments) when is_map(assignments) do
    # Fallback for factions that have no OC 2.0 crimes stored in the database
    assignments
  end

  def reassign_teams([] = _teams, _crimes, assignments) when is_map(assignments) do
    assignments
  end

  @spec filter_team_crimes(team :: Tornium.Schema.OrganizedCrimeTeam.t(), crimes :: [Tornium.Schema.OrganizedCrime.t()]) ::
          [Tornium.Schema.OrganizedCrime.t()]
  defp filter_team_crimes(
         %Tornium.Schema.OrganizedCrimeTeam{oc_name: oc_name} = team,
         [%Tornium.Schema.OrganizedCrime{} | _remaining_crimes] = crimes
       ) do
    crimes
    |> Enum.filter(fn %Tornium.Schema.OrganizedCrime{oc_name: name, status: status} ->
      oc_name == name and status == :recruiting
    end)
    |> Enum.filter(fn %Tornium.Schema.OrganizedCrime{slots: slots} ->
      # Filter out OCs where slots are contain users not in the team
      Enum.all?(slots, fn %Tornium.Schema.OrganizedCrimeSlot{user_id: user_id} ->
        is_nil(user_id) or Enum.member?(team_member_ids(team), user_id)
      end)
    end)
    |> Enum.sort_by(fn %Tornium.Schema.OrganizedCrime{slots: slots, expires_at: expires_at} ->
      {
        Enum.count(slots, fn %Tornium.Schema.OrganizedCrimeSlot{user_id: user_id} -> not is_nil(user_id) end),
        expires_at
      }
    end)
  end

  @doc """
  Assign a specific organized crime team to a specific organized crime.

  Returns a tuple of the remaining OCs to be assigned and a map of OC team assignments (see
  `Tornium.Faction.OC.Team.new_team_assignments()`). If there is no OC that can be assigned
  to the OC team, `{:spawn_required, oc_name}` will be added to the assignments map without
  removing any OCs from the list to be assigned.
  """
  @spec do_assign_team(
          crime :: Tornium.Schema.OrganizedCrime.t() | nil,
          crimes :: [Tornium.Schema.OrganizedCrime.t()],
          team :: Tornium.Schema.OrganizedCrimeTeam.t(),
          assignments :: new_team_assignments()
        ) :: {[Tornium.Schema.OrganizedCrime.t()], new_team_assignments()}
  def do_assign_team(
        %Tornium.Schema.OrganizedCrime{} = crime,
        [%Tornium.Schema.OrganizedCrime{} | _remaining_crimes] = crimes,
        %Tornium.Schema.OrganizedCrimeTeam{} = team,
        %{} = assignments
      ) do
    {List.delete(crimes, crime), Map.put(assignments, team, crime)}
  end

  def do_assign_team(
        nil = _crime,
        [%Tornium.Schema.OrganizedCrime{} | _remaining_crimes] = crimes,
        %Tornium.Schema.OrganizedCrimeTeam{oc_name: oc_name} = team,
        %{} = assignments
      ) do
    {crimes, Map.put(assignments, team, {:spawn_required, oc_name})}
  end

  @doc """
  Update all newly assigned organized crime teams in the DB.

  OC teams that require an OC to be spawned will have their `required_spawn_at` timestamp updated.
  """
  @spec update_assigned_teams(check_struct :: Tornium.Faction.OC.Team.Check.Struct.t()) ::
          Tornium.Faction.OC.Team.Check.Struct.t()
  def update_assigned_teams(
        %Tornium.Faction.OC.Team.Check.Struct{assigned_team: assigned_team, team_spawn_required: team_spawn_required} =
          check_struct
      ) do
    Enum.each(assigned_team, fn {team, crime} -> Tornium.Schema.OrganizedCrime.update_assigned_team(team, crime) end)

    Enum.each(team_spawn_required, fn team ->
      Tornium.Schema.OrganizedCrimeTeam.update_spawn_required(team)
    end)

    check_struct
  end

  @doc """
  Get the user IDs of the users composing the OC team.

  The function will return the user IDs of OC team members when provided an OC team or a list of OC
  team members. The returned list of OC team members IDs will include wildcard members which are 
  represented by `nil`.
  """
  @spec team_member_ids(team :: Tornium.Schema.OrganizedCrimeTeam.t()) :: [non_neg_integer() | nil]
  def team_member_ids(%Tornium.Schema.OrganizedCrimeTeam{members: members} = _team) when is_list(members) do
    team_member_ids(members)
  end

  @spec team_member_ids(members :: [Tornium.Schema.OrganizedCrimeTeamMember.t()]) :: [non_neg_integer() | nil]
  def team_member_ids([%Tornium.Schema.OrganizedCrimeTeamMember{} | _remaining_members] = members) do
    Enum.map(members, fn %Tornium.Schema.OrganizedCrimeTeamMember{user_id: user_id} -> user_id end)
  end

  def team_member_ids(members) when members == [] do
    []
  end

  @doc """
  Execute the checks in `Tornium.Faction.OC.Team.Check`.

  Executes the checks of `Tornium.Faction.OC.Team.Checks` against an list of OC teams and their assigned OCs
  to create a `Tornium.Faction.OC.Team.Check.Struct` state that contains the teams or OC triggering each
  check. The checks performed by this function are not the exhaustive list contained by
  `Tornium.Faction.OC.Team.Check.Struct` as the team assignments are performed before the checks are performed.
  """
  @spec check(
          team_list :: [Tornium.Schema.OrganizedCrimeTeam.t()],
          config :: Tornium.Schema.ServerOCConfig.t() | nil,
          crimes :: [Tornium.Schema.OrganizedCrime.t()],
          team_checks :: Tornium.Faction.OC.Team.Check.Struct.t() | nil
        ) :: Tornium.Faction.OC.Team.Check.Struct.t()
  def check(team_list, config, crimes, team_checks \\ nil)

  def check(team_list, config, crimes, team_checks) when is_list(team_list) and is_nil(team_checks) do
    check(team_list, config, crimes, Tornium.Faction.OC.Team.Check.Struct.new())
  end

  def check(
        [%Tornium.Schema.OrganizedCrimeTeam{} = team | remaining_teams],
        %Tornium.Schema.ServerOCConfig{} = config,
        [%Tornium.Schema.OrganizedCrime{} = _crime | _remaining_crimes] = crimes,
        %Tornium.Faction.OC.Team.Check.Struct{} = team_checks
      ) do
    team_checks =
      team_checks
      |> Tornium.Faction.OC.Team.Check.check_member_join_required(team)
      |> Tornium.Faction.OC.Team.Check.check_member_incorrect_crime(team, crimes)
      |> Tornium.Faction.OC.Team.Check.check_incorrect_member(team)
      |> Tornium.Faction.OC.Team.Check.check_member_incorrect_slot(team)

    check(remaining_teams, config, team_checks)
  end

  def check(_team_list, _config, _crimes, %Tornium.Faction.OC.Team.Check.Struct{} = team_checks) do
    # Fallback; OR
    # Skip all OC team checks when a configuration from a server is required (currently all checks)

    team_checks
  end
end
