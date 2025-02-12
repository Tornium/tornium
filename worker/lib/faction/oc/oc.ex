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

defmodule Tornium.Faction.OC do
  alias Tornium.Utils

  @doc ~S"""
  Determine whether a faction has migrated to Organized Crimes 2.0 by the shape of the API response. A faction that has migrated will have a response that is a list while one that has not will have a map.
  """
  @spec migrated?(data :: map()) :: boolean()
  def migrated?(%{"crimes" => crimes}) when is_map(crimes) do
    false
  end

  def migrated?(%{"crimes" => crimes}) when is_list(crimes) do
    true
  end

  # TODO: Document this function
  # TODO: Test this function
  @spec parse(
          api_data :: map() | list(map()),
          faction_id :: integer(),
          crimes :: list(Tornium.Schema.OrganizedCrime.t())
        ) ::
          list(Tornium.Schema.OrganizedCrime.t())
  def parse(api_data, faction_id, crimes \\ [])

  def parse(%{"crimes" => crime_data}, faction_id, crimes) when is_list(crime_data) do
    # Parse the crime data from the API response
    parse(crime_data, faction_id, crimes)
  end

  def parse(%{"crimes" => crime_data}, _faction_id, _crimes) when is_map(crime_data) do
    # Faction is still on OCs 1.0
    []
  end

  def parse(
        [
          %{
            "id" => oc_id,
            "name" => oc_name,
            "difficulty" => oc_difficulty,
            "status" => status,
            "created_at" => created_at,
            "planning_at" => planning_started_at,
            "ready_at" => ready_at,
            "expired_at" => expires_at,
            "executed_at" => executed_at,
            "slots" => slots
          } = _crime
          | remaining_crimes
        ],
        faction_id,
        crimes
      ) do
    status =
      status
      |> String.downcase()
      |> String.to_atom()

    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: oc_id,
      oc_name: oc_name,
      oc_difficulty: oc_difficulty,
      faction_id: faction_id,
      status: status,
      created_at: Utils.unix_to_timestamp(created_at),
      planning_started_at: Utils.unix_to_timestamp(planning_started_at),
      ready_at: Utils.unix_to_timestamp(ready_at),
      expires_at: Utils.unix_to_timestamp(expires_at),
      executed_at: Utils.unix_to_timestamp(executed_at),
      slots: parse_slots(slots, oc_id)
    }

    parse(remaining_crimes, faction_id, [crime | crimes])
  end

  def parse([], _faction_id, crimes) do
    crimes
  end

  # TODO: Document this function
  @spec parse_slots(
          slots_to_parse :: list(map()),
          oc_id :: integer(),
          slots :: list(Tornium.Schema.OrganizedCrimeSlot.t())
        ) ::
          list(Tornium.Schema.OrganizedCrimeSlot.t())
  def parse_slots(slots_to_parse, oc_id, slots \\ [])

  def parse_slots(
        [
          %{
            "position" => crime_position,
            "item_requirement" => nil,
            "user_id" => user_id,
            "success_chance" => user_success_chance
          } = _slot
          | remaining_slots
        ],
        oc_id,
        slots
      ) do
    slot = %Tornium.Schema.OrganizedCrimeSlot{
      oc_id: oc_id,
      crime_position: crime_position,
      user_id: user_id,
      user_success_chance: user_success_chance,
      item_required_id: nil,
      item_available: nil
    }

    parse_slots(remaining_slots, oc_id, [slot | slots])
  end

  def parse_slots(
        [
          %{
            "position" => crime_position,
            "item_requirement" => %{"id" => item_id, "is_available" => item_available},
            "user_id" => user_id,
            "success_chance" => user_success_chance
          } = _slot
          | remaining_slots
        ],
        oc_id,
        slots
      ) do
    slot = %Tornium.Schema.OrganizedCrimeSlot{
      oc_id: oc_id,
      crime_position: crime_position,
      user_id: user_id,
      user_success_chance: user_success_chance,
      item_required_id: item_id,
      item_available: item_available
    }

    parse_slots(remaining_slots, oc_id, [slot | slots])
  end

  def parse_slots([], _oc_id, slots) do
    slots
  end

  @spec check(oc_list :: [Tornium.Schema.OrganizedCrime.t()]) :: Tornium.Faction.OC.Check.Struct.t()
  def check(oc_list, oc_checks \\ nil)

  def check(oc_list, oc_checks) when is_list(oc_list) and is_nil(oc_checks) do
    check(oc_list, Tornium.Faction.OC.Check.Struct.new())
  end

  def check([%Tornium.Schema.OrganizedCrime{} = oc | remaining_oc], oc_checks) do
    oc_checks =
      oc_checks
      |> Tornium.Faction.OC.Check.check_tools(oc)

    check(remaining_oc, oc_checks)
  end

  def check([], oc_checks) do
    oc_checks
  end
end
