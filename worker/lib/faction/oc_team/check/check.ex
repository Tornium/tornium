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

defmodule Tornium.Faction.OC.Team.Check do
  @moduledoc """
  Execute checks against a faction's organized crime team to determine if the OC teams are in invalid states.

  These checks can determine the invalid states:
    - `:team_member_join_required`: Team member needs to join the assigned OC (`Tornium.Faction.OC.Team.Check.check_member_join_required/2`)
    - `:team_member_incorrect_crime`: Team member is in the wrong OC (`Tornium.Faction.OC.Team.Check.check_member_incorrect_crime/3`)
    - `:team_incorrect_member`: Assigned OC contains a member not of the OC team (`Tornium.Faction.OC.Team.Check.check_incorrect_member/2`)
    - `:team_member_incorrect_slot`: Team member is in the wrong slot of the OC (`Tornium.Faction.OC.Team.Check.check_member_incorrect_slot/2`)

  These checks update and return the combined state of the checks, `Tornium.Faction.OC.Team.Check.Struct`, and
  can be piped into each other.
  """

  @type state :: Tornium.Faction.OC.Team.Check.Struct.t()

  @doc """
  Check if any member of the OC team is not in the OC.

  Determine which members of the Organized Crime team are not in slots of the OC. OC team members not in the
  OC will be added to the check state.

  **NOTE:** This will ignore OC members that are in the OC but in the wrong slot as the `:team_member_incorrect_slot`
  check will handle that.
  """
  @spec check_member_join_required(check_state :: state(), team :: Tornium.Schema.OrganizedCrimeTeam.t()) :: state()
  def check_member_join_required(
        %Tornium.Faction.OC.Team.Check.Struct{} = check_state,
        %Tornium.Schema.OrganizedCrimeTeam{current_crime: current_crime} = _team
      )
      when is_nil(current_crime) do
    # No OC is assigned to the team
    check_state
  end

  def check_member_join_required(
        %Tornium.Faction.OC.Team.Check.Struct{team_member_join_required: team_member_join_required} = check_state,
        %Tornium.Schema.OrganizedCrimeTeam{members: members, current_crime: current_crime} = _team
      ) do
    new_member_join_assignments =
      for %Tornium.Schema.OrganizedCrimeTeamMember{} = member <- members,
          not member_in_crime?(member, current_crime),
          do: {member, current_crime}

    %Tornium.Faction.OC.Team.Check.Struct{
      check_state
      | team_member_join_required: [new_member_join_assignments | team_member_join_required] |> List.flatten()
    }
  end

  @doc """
  Determine if a OC team member is in an OC.

  **NOTE:** Wildcard team members will not be handled by this.

  ## Examples

    iex> Tornium.Faction.OC.Team.Check.member_in_crime?(
    ...>   %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1},
    ...>   %Tornium.Schema.OrganizedCrime{slots: []}
    ...> )
    false

    iex> Tornium.Faction.OC.Team.Check.member_in_crime?(
    ...>   %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1},
    ...>   %Tornium.Schema.OrganizedCrime{slots: [%Tornium.Schema.OrganizedCrimeSlot{user_id: 1}]}
    ...> )
    true
  """
  @spec member_in_crime?(
          member :: Tornium.Schema.OrganizedCrimeTeamMember.t(),
          assigned_crime :: Tornium.Schema.OrganizedCrime.t()
        ) :: boolean()
  def member_in_crime?(
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: member_id} = _member,
        %Tornium.Schema.OrganizedCrime{slots: slots} = _assigned_crime
      ) do
    Enum.any?(slots, fn %Tornium.Schema.OrganizedCrimeSlot{user_id: user_id} -> user_id == member_id end)
  end

  @doc """
  Determine if any member of the OC team is in any OC other than the OC assigned to the OC team.
  """
  @spec check_member_incorrect_crime(
          check_state :: state(),
          team :: Tornium.Schema.OrganizedCrimeTeam.t(),
          crimes :: [Tornium.Schema.OrganizedCrime.t()]
        ) :: state()
  def check_member_incorrect_crime(
        %Tornium.Faction.OC.Team.Check.Struct{team_member_incorrect_crime: team_member_incorrect_crime} = check_state,
        %Tornium.Schema.OrganizedCrimeTeam{current_crime: assigned_crime, members: members} = _team,
        crimes
      )
      when is_list(crimes) do
    new_member_incorrect_crime_assignments =
      for %Tornium.Schema.OrganizedCrimeTeamMember{} = member <- members,
          incorrect_member_crime = find_incorrect_crime(member, crimes),
          not is_nil(incorrect_member_crime),
          do: {member, incorrect_member_crime, assigned_crime}

    %Tornium.Faction.OC.Team.Check.Struct{
      check_state
      | team_member_incorrect_crime:
          [new_member_incorrect_crime_assignments | team_member_incorrect_crime] |> List.flatten()
    }
  end

  @doc """
  Find an OC the OC team member is in that is not the OC assigned to the member's OC team.
  """
  @spec find_incorrect_crime(
          member :: Tornium.Schema.OrganizedCrimeTeamMember.t(),
          crimes :: [Tornium.Schema.OrganizedCrime.t()]
        ) :: Tornium.Schema.OrganizedCrime.t() | nil
  def find_incorrect_crime(%Tornium.Schema.OrganizedCrimeTeamMember{team_id: team_id} = member, crimes)
      when is_list(crimes) do
    Enum.find(crimes, fn %Tornium.Schema.OrganizedCrime{assigned_team_id: assigned_team_id} = crime ->
      assigned_team_id != team_id and member_in_crime?(member, crime)
    end)
  end

  @doc """
  Determine if any slot of the OC assigned to the OC team is not a member of the OC team.

  If the slot filled is for a wildcard member of the OC team, the slot will be skipped as wildcard slots can
  be filled by anyone.
  """
  @spec check_incorrect_member(check_state :: state(), team :: Tornium.Schema.OrganizedCrimeTeam.t()) :: state()
  def check_incorrect_member(
        %Tornium.Faction.OC.Team.Check.Struct{} = check_state,
        %Tornium.Schema.OrganizedCrimeTeam{current_crime: assigned_crime} = _team
      )
      when is_nil(assigned_crime) do
    # Fallback for no assigned OC for the team
    check_state
  end

  def check_incorrect_member(
        %Tornium.Faction.OC.Team.Check.Struct{team_incorrect_member: team_incorrect_member} = check_state,
        %Tornium.Schema.OrganizedCrimeTeam{current_crime: assigned_crime, members: members} = team
      ) do
    new_incorrect_member_assignments =
      for %Tornium.Schema.OrganizedCrimeSlot{
            crime_position: crime_position,
            crime_position_index: crime_position_index,
            user_id: slot_user_id
          } = slot <- assigned_crime.slots,
          slot_member =
            Tornium.Schema.OrganizedCrimeTeamMember.find_slot_member(members, crime_position, crime_position_index),
          not is_nil(slot_member) and not Tornium.Schema.OrganizedCrimeTeamMember.wildcard?(slot_member) and
            slot_user_id != slot_member.user_id and not Tornium.Schema.OrganizedCrimeTeam.member?(team, slot_user_id),
          do: {slot, assigned_crime}

    %Tornium.Faction.OC.Team.Check.Struct{
      check_state
      | team_incorrect_member: [new_incorrect_member_assignments | team_incorrect_member] |> List.flatten()
    }
  end

  @doc """
  Determine if any member of the OC team is in the assigned OC but in the incorrect slot.
  """
  @spec check_member_incorrect_slot(
          check_state :: state(),
          team :: Tornium.Schema.OrganizedCrimeTeam.t()
        ) :: state()
  def check_member_incorrect_slot(
        %Tornium.Faction.OC.Team.Check.Struct{} = check_state,
        %Tornium.Schema.OrganizedCrimeTeam{current_crime: assigned_crime} = _team
      )
      when is_nil(assigned_crime) do
    check_state
  end

  def check_member_incorrect_slot(
        %Tornium.Faction.OC.Team.Check.Struct{team_member_incorrect_slot: team_member_incorrect_slot} = check_state,
        %Tornium.Schema.OrganizedCrimeTeam{
          current_crime: %Tornium.Schema.OrganizedCrime{slots: assigned_crime_slots},
          members: members
        } = team
      )
      when is_list(members) do
    new_member_incorrect_slot_assignments =
      for %Tornium.Schema.OrganizedCrimeSlot{
            crime_position: slot_position,
            crime_position_index: slot_position_index,
            user_id: slot_user_id
          } = slot <- assigned_crime_slots,
          slot_member =
            Tornium.Schema.OrganizedCrimeTeamMember.find_slot_member(members, slot_position, slot_position_index),
          not is_nil(slot_member) and not Tornium.Schema.OrganizedCrimeTeamMember.wildcard?(slot_member) and
            slot_member.user_id != slot_user_id and Tornium.Schema.OrganizedCrimeTeam.member?(team, slot_user_id),
          do: {slot_member, slot}

    %Tornium.Faction.OC.Team.Check.Struct{
      check_state
      | team_member_incorrect_slot:
          [new_member_incorrect_slot_assignments | team_member_incorrect_slot] |> List.flatten()
    }
  end
end
