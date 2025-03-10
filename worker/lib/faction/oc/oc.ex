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

  @doc ~S"""
  Parse an API response into a list of Organized Crime 2.0 crimes including the slots of the crimes.
  """
  @spec parse(
          api_data :: map() | Tornex.API.error(),
          faction_id :: integer(),
          crimes :: [Tornium.Schema.OrganizedCrime.t()]
        ) ::
          [Tornium.Schema.OrganizedCrime.t()]
  def parse(api_data, faction_id, crimes \\ [])

  def parse({:error, _}, _faction_id, _crimes) do
    # Encountered any issues with the Torn API
    []
  end

  def parse(%{"crimes" => crime_data, "members" => members}, faction_id, crimes)
      when is_list(crime_data) and is_list(members) do
    # Parse the crime data from the API response
    parse_crimes(crime_data, members, faction_id, crimes)
  end

  def parse(%{"crimes" => crime_data}, _faction_id, _crimes) when is_map(crime_data) do
    # Faction is still on OCs 1.0
    []
  end

  def parse(_api_data, _faction_id, _crimes) do
    # API error fallback
    []
  end

  @doc ~S"""
  Parse the crimes from the API response into a list of organized crimes including the slots of the crimes.
  """
  @spec parse_crimes(
          api_crimes :: [map()],
          api_members :: [map()],
          faction_id :: integer(),
          crimes :: [Tornium.Schema.OrganizedCrime.t()]
        ) :: [Tornium.Schema.OrganizedCrime.t()]
  def parse_crimes(
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
        api_members,
        faction_id,
        crimes
      ) do
    status =
      status
      |> String.downcase()
      |> String.to_atom()

    {ready_at_ts, oc_ready} =
      case {status, ready_at} do
        {:planning, _} when not is_nil(ready_at) ->
          # This should only trigger on OCs that are still in the planning stage but are past the `ready_at`
          # timestamp to make sure that the delay notifications don't trigger before the OC is ready.
          ready_at_ts = Utils.unix_to_timestamp(ready_at)
          {ready_at_ts, DateTime.after?(DateTime.utc_now(), ready_at_ts)}

        {_, _} ->
          {Utils.unix_to_timestamp(ready_at), false}
      end

    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: oc_id,
      oc_name: oc_name,
      oc_difficulty: oc_difficulty,
      faction_id: faction_id,
      status: status,
      created_at: Utils.unix_to_timestamp(created_at),
      planning_started_at: Utils.unix_to_timestamp(planning_started_at),
      ready_at: ready_at_ts,
      expires_at: Utils.unix_to_timestamp(expires_at),
      executed_at: Utils.unix_to_timestamp(executed_at),
      slots: parse_slots(slots, api_members, oc_id, oc_ready)
    }

    parse_crimes(remaining_crimes, api_members, faction_id, [crime | crimes])
  end

  def parse_crimes([], _api_members, _faction_id, crimes) do
    crimes
  end

  def parse_crimes(_, _api_members, _faction_id, _crimes) do
    # Fallback for errors from the Torn API
    []
  end

  # TODO: Write test for this function
  @doc ~S"""
  Parse the API data for an Organized Crime 2.0 crime for the list of the crime's slots.
  """
  @spec parse_slots(
          slots_to_parse :: [map()],
          members :: [map()],
          oc_id :: integer(),
          oc_ready :: boolean(),
          slots :: [Tornium.Schema.OrganizedCrimeSlot.t()]
        ) ::
          [Tornium.Schema.OrganizedCrimeSlot.t()]
  def parse_slots(slots_to_parse, members, oc_id, oc_ready, slots \\ [])

  def parse_slots(
        [
          %{
            "position" => crime_position,
            "item_requirement" => item_requirement,
            "user_id" => user_id,
            "success_chance" => user_success_chance
          } = _slot
          | remaining_slots
        ],
        members,
        oc_id,
        oc_ready,
        slots
      )
      when is_list(members) and is_boolean(oc_ready) and (is_map(item_requirement) or is_nil(item_requirement)) do
    slot =
      %Tornium.Schema.OrganizedCrimeSlot{
        slot_index: Kernel.length(slots),
        oc_id: oc_id,
        crime_position: crime_position,
        user_id: user_id,
        user_success_chance: user_success_chance
      }
      |> put_item_required(item_requirement)
      |> put_delayer(members, oc_ready)

    # FIXME: members is of type `maybe_improper_list` instead of `[map()]`

    parse_slots(remaining_slots, members, oc_id, oc_ready, [slot | slots])
  end

  def parse_slots([], _members, _oc_id, _oc_ready, slots) do
    slots
  end

  @spec put_item_required(slot :: Tornium.Schema.OrganizedCrimeSlot.t(), item_requirement :: map() | nil) ::
          Tornium.Schema.OrganizedCrimeSlot.t()
  defp put_item_required(%Tornium.Schema.OrganizedCrimeSlot{} = slot, item_requirement) when is_nil(item_requirement) do
    slot
    |> Map.put(:item_required_id, nil)
    |> Map.put(:item_available, false)
  end

  defp put_item_required(%Tornium.Schema.OrganizedCrimeSlot{} = slot, %{
         "id" => item_id,
         "is_available" => item_available
       }) do
    slot
    |> Map.put(:item_required_id, item_id)
    |> Map.put(:item_available, item_available)
  end

  @spec put_delayer(slot :: Tornium.Schema.OrganizedCrimeSlot.t(), members :: [map()], oc_ready :: boolean()) ::
          Tornium.Schema.OrganizedCrimeSlot.t()
  defp put_delayer(%Tornium.Schema.OrganizedCrimeSlot{user_id: user_id} = slot, members, true)
       when not is_nil(user_id) do
    member = Enum.find(members, fn m -> m["id"] == user_id end)

    {delayer, delayed_reason} =
      case member["status"]["description"] do
        "Okay" -> {false, nil}
        other_status -> {true, other_status}
      end

    slot
    |> Map.put(:delayer, delayer)
    |> Map.put(:delayed_reason, delayed_reason)
  end

  defp put_delayer(%Tornium.Schema.OrganizedCrimeSlot{} = slot, _members, false) do
    slot
    |> Map.put(:delayer, false)
    |> Map.put(:delayed_reason, nil)
  end

  @doc ~S"""
  Execute the checks in `Tornium.Faction.OC.Check` against an list of Organized Crimes to create a `Tornium.Faction.OC.Check.Struct` state that contains the slots or crimes triggering each check.
  """
  @spec check(oc_list :: [Tornium.Schema.OrganizedCrime.t()]) :: Tornium.Faction.OC.Check.Struct.t()
  def check(oc_list, oc_checks \\ nil)

  def check(oc_list, oc_checks) when is_list(oc_list) and is_nil(oc_checks) do
    check(oc_list, Tornium.Faction.OC.Check.Struct.new())
  end

  def check([%Tornium.Schema.OrganizedCrime{} = oc | remaining_oc], oc_checks) do
    oc_checks =
      oc_checks
      |> Tornium.Faction.OC.Check.check_tools(oc)
      |> Tornium.Faction.OC.Check.check_delayers(oc)

    check(remaining_oc, oc_checks)
  end

  def check([], oc_checks) do
    oc_checks
  end
end
