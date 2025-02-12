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
  @type state :: Tornium.Faction.OC.Check.Struct.t()

  @doc ~S"""
  Check the slots for an Organized Crime to determine if any of the slots are missing any of the required tools. If a tool is missing, update `Tornium.Faction.OC.Check.Struct` with the slot missing the tool.
  """
  @spec check_tools(check_state :: state(), crime :: Tornium.Schema.OrganizedCrime.t()) :: state
  def check_tools(check_state, %Tornium.Schema.OrganizedCrime{slots: slots, status: status} = _crime) do
    case status do
      :recruiting -> check_slot_tool(slots, check_state)
      :planning -> check_slot_tool(slots, check_state)
      _ -> check_state
    end
  end

  @spec check_slot_tool([Tornium.Schema.OrganizedCrimeSlot.t()], state()) :: state()
  defp check_slot_tool(
         [
           %Tornium.Schema.OrganizedCrimeSlot{user_id: user, item_required: item, item_available: false} = slot
           | remaining_slots
         ],
         %Tornium.Faction.OC.Check.Struct{missing_tools: missing_tools} = state
       )
       when not is_nil(item) and not is_nil(user) do
    # TODO: Skip when the noticication has already been sent
    state = Map.replace(state, :missing_tools, [slot | missing_tools])
    check_slot_tool(remaining_slots, state)
  end

  defp check_slot_tool([_slot | remaining_slots], state) do
    check_slot_tool(remaining_slots, state)
  end

  defp check_slot_tool([], state) do
    state
  end
end
