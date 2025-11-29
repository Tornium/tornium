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

defmodule Tornium.Faction.OC.Check do
  @moduledoc ~S"""
  Execute checks against a faction's organized crimes to determine if the OCs are in invalid states.

  These checks can determine the invalid states:
    - Slot missing a tool/material (`Tornium.Faction.OC.check_tools/2`)
    - Slot delaying the initiation of the OC (`Tornium.Faction.OC.check_delayers/2`)

  These checks update and return the combined state of the checks, `Tornium.Faction.OC.Check.Struct`, and can be piped into each other.
  """

  @type state :: Tornium.Faction.OC.Check.Struct.t()

  # TODO: Determine if the expires_at time also needs to be validated before performing the checks

  @doc ~S"""
  Check the slots for an Organized Crime to determine if any of the slots are missing any of the required tools. This only affects organized crimes that are within 24 hours of being ready. If a tool is missing, update `Tornium.Faction.OC.Check.Struct` with the slot missing the tool.
  """
  @spec check_tools(check_state :: state(), crime :: Tornium.Schema.OrganizedCrime.t()) :: state()
  def check_tools(
        check_state,
        %Tornium.Schema.OrganizedCrime{ready_at: ready_at, slots: slots, status: :planning} = _crime
      )
      when not is_nil(ready_at) do
    if DateTime.diff(ready_at, DateTime.utc_now(), :hour) <= 24 do
      check_slot_tool(slots, check_state)
    else
      check_state
    end
  end

  def check_tools(check_state, %Tornium.Schema.OrganizedCrime{} = _crime) do
    check_state
  end

  @doc ~S"""
  Check the slots for an Organized Crime to determine if any of the slots' members are not okay once the OC is ready. If the member is delaying the OC, update `Tornium.Faction.OC.Check.Struct` with the slot delaying the OC.
  """
  @spec check_delayers(check_state :: state(), crime :: Tornium.Schema.OrganizedCrime.t()) :: state()
  def check_delayers(check_state, %Tornium.Schema.OrganizedCrime{ready_at: ready_at, slots: slots} = _crime)
      when not is_nil(ready_at) do
    if DateTime.after?(DateTime.utc_now(), ready_at) do
      check_slot_delayer(slots, check_state)
    else
      check_state
    end
  end

  def check_delayers(check_state, %Tornium.Schema.OrganizedCrime{} = _crime) do
    check_state
  end

  @doc """
  Check the slots of an Organized Crime to determine if any of the slots have a CPR outside of a specified range. The range is provided by a server's configuration with a global range and an optional per-OC name local range. If a member is outside of that range, update `Tornium.Faction.OC.Check.Struct` with the slot outside the range.
  """
  @spec check_extra_range(
          check_state :: state(),
          crime :: Tornium.Schema.OrganizedCrime.t(),
          config :: Tornium.Schema.ServerOCConfig.t()
        ) :: state()
  def check_extra_range(
        check_state,
        %Tornium.Schema.OrganizedCrime{} = _crime,
        %Tornium.Schema.ServerOCConfig{extra_range_channel: nil} = _config
      ) do
    # As this cheeck depends on a server's configuration, skip the check if the feature is disabled.
    # Then if the feature is later enabled, the check can be run then.
    check_state
  end

  def check_extra_range(
        check_state,
        %Tornium.Schema.OrganizedCrime{ready_at: ready_at, slots: slots} = _crime,
        %Tornium.Schema.ServerOCConfig{} = config
      ) do
    # OCs that have already been completed are pointless to be checked
    if is_nil(ready_at) or DateTime.after?(ready_at, DateTime.utc_now()) do
      check_slot_extra_range(slots, check_state, config)
    else
      check_state
    end
  end

  @spec check_slot_tool([Tornium.Schema.OrganizedCrimeSlot.t()], state()) :: state()
  defp check_slot_tool(
         [%Tornium.Schema.OrganizedCrimeSlot{sent_tool_notification: true} = _slot | remaining_slots],
         %Tornium.Faction.OC.Check.Struct{} = state
       ) do
    # Skip slots that have already had a notification sent for them
    check_slot_tool(remaining_slots, state)
  end

  defp check_slot_tool(
         [
           %Tornium.Schema.OrganizedCrimeSlot{user_id: user, item_required_id: item_id, item_available: false} = slot
           | remaining_slots
         ],
         %Tornium.Faction.OC.Check.Struct{missing_tools: missing_tools} = state
       )
       when not is_nil(item_id) and not is_nil(user) do
    state = Map.replace(state, :missing_tools, [slot | missing_tools])
    check_slot_tool(remaining_slots, state)
  end

  defp check_slot_tool([_slot | remaining_slots], state) do
    check_slot_tool(remaining_slots, state)
  end

  defp check_slot_tool([], state) do
    state
  end

  @spec check_slot_delayer([Tornium.Schema.OrganizedCrimeSlot.t()], state()) :: state()
  defp check_slot_delayer(
         [%Tornium.Schema.OrganizedCrimeSlot{sent_delayer_notification: true} = _slot | remaining_slots],
         %Tornium.Faction.OC.Check.Struct{} = state
       ) do
    # Skip slots that have already had a notification sent for them
    check_slot_delayer(remaining_slots, state)
  end

  defp check_slot_delayer(
         [%Tornium.Schema.OrganizedCrimeSlot{delayer: true} = slot | remaining_slots],
         %Tornium.Faction.OC.Check.Struct{delayers: delayers} = state
       ) do
    state = Map.replace(state, :delayers, [slot | delayers])
    check_slot_delayer(remaining_slots, state)
  end

  defp check_slot_delayer([_slot | remaining_slots], state) do
    check_slot_delayer(remaining_slots, state)
  end

  defp check_slot_delayer([], state) do
    state
  end

  @spec check_slot_extra_range(
          [Tornium.Schema.OrganizedCrimeSlot.t()],
          state :: state(),
          config :: Tornium.Schema.ServerOCConfig.t()
        ) :: state()
  defp check_slot_extra_range(
         [%Tornium.Schema.OrganizedCrimeSlot{sent_extra_range_notification: true} = _slot | remaining_slots],
         %Tornium.Faction.OC.Check.Struct{} = state,
         %Tornium.Schema.ServerOCConfig{} = config
       ) do
    check_slot_extra_range(remaining_slots, state, config)
  end

  defp check_slot_extra_range(
         [
           %Tornium.Schema.OrganizedCrimeSlot{user_id: nil} = _slot
           | remaining_slots
         ],
         %Tornium.Faction.OC.Check.Struct{} = state,
         %Tornium.Schema.ServerOCConfig{} = config
       ) do
    check_slot_extra_range(remaining_slots, state, config)
  end

  defp check_slot_extra_range(
         [
           %Tornium.Schema.OrganizedCrimeSlot{oc: %Tornium.Schema.OrganizedCrime{}, user_success_chance: chance} = slot
           | remaining_slots
         ],
         %Tornium.Faction.OC.Check.Struct{extra_range: extra_range} = state,
         %Tornium.Schema.ServerOCConfig{} = config
       ) do
    {minimum, maximum} =
      Tornium.Schema.ServerOCConfig.chance_range(config, slot.oc)

    if chance < minimum or chance > maximum do
      state = Map.replace(state, :extra_range, [slot | extra_range])
      check_slot_extra_range(remaining_slots, state, config)
    else
      check_slot_extra_range(remaining_slots, state, config)
    end
  end

  defp check_slot_extra_range([], %Tornium.Faction.OC.Check.Struct{} = state, _config) do
    state
  end
end
