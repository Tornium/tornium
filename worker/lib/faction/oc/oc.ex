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

  @doc """
  Determine whether a faction has migrated to Organized Crimes 2.0 by the shape of the API response.
  A faction that has migrated will have a response that is a list while one that has not will have a map.
  """
  @spec migrated?(data :: map()) :: boolean()
  def migrated?(%{"crimes" => crimes}) when is_map(crimes) do
    false
  end

  def migrated?(%{"crimes" => crimes}) when is_list(crimes) do
    true
  end

  @doc """
  Parse an API response into a list of Organized Crime 2.0 crimes including the slots of the crimes.
  """
  @spec parse(
          crimes_data :: [Torngen.Client.Schema.FactionCrime.t()],
          members_data :: [Torngen.Client.Schema.FactionMember.t()],
          faction_id :: pos_integer(),
          crimes :: [Tornium.Schema.OrganizedCrime.t()]
        ) ::
          [Tornium.Schema.OrganizedCrime.t()]
  def parse(crimes_data, members_data, faction_id, crimes \\ [])

  def parse(
        [
          %Torngen.Client.Schema.FactionCrime{
            id: oc_id,
            name: oc_name,
            difficulty: oc_difficulty,
            status: status,
            created_at: created_at,
            planning_at: planning_started_at,
            ready_at: ready_at,
            expired_at: expires_at,
            executed_at: executed_at,
            slots: slots
          }
          | remaining_crimes
        ] = _crimes_data,
        members_data,
        faction_id,
        crimes
      )
      when is_list(members_data) and is_integer(faction_id) do
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
      slots: parse_slots(slots, members_data, oc_id, oc_ready)
    }

    parse(remaining_crimes, members_data, faction_id, [crime | crimes])
  end

  def parse([] = _crimes_data, members_data, faction_id, crimes)
      when is_list(members_data) and is_integer(faction_id) do
    crimes
  end

  # TODO: Write test for this function
  @doc """
  Parse the API data for an Organized Crime 2.0 crime for the list of the crime's slots.
  """
  @spec parse_slots(
          slots_to_parse :: [Torngen.Client.Schema.FactionCrimeSlot.t()],
          members :: [Torngen.Client.Schema.FactionMember.t()],
          oc_id :: integer(),
          oc_ready :: boolean(),
          slots :: [Tornium.Schema.OrganizedCrimeSlot.t()]
        ) ::
          [Tornium.Schema.OrganizedCrimeSlot.t()]
  def parse_slots(slots_to_parse, members, oc_id, oc_ready, slots \\ [])

  def parse_slots(
        [
          %Torngen.Client.Schema.FactionCrimeSlot{
            position: crime_position,
            position_info: %Torngen.Client.Schema.FactionSlotPositionInfo{
              id: "P" <> slot_index,
              number: crime_position_index
            },
            item_requirement: item_requirement,
            user: %Torngen.Client.Schema.FactionCrimeUser{id: user_id, joined_at: user_joined_at},
            checkpoint_pass_rate: user_success_chance
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
        slot_index: String.to_integer(slot_index) - 1,
        oc_id: oc_id,
        crime_position: crime_position,
        crime_position_index: crime_position_index,
        user_id: user_id,
        user_success_chance: user_success_chance,
        user_joined_at: Utils.unix_to_timestamp(user_joined_at)
      }
      |> put_item_required(item_requirement)
      |> put_delayer(members, oc_ready)

    parse_slots(remaining_slots, members, oc_id, oc_ready, [slot | slots])
  end

  def parse_slots(
        [
          %Torngen.Client.Schema.FactionCrimeSlot{
            position: crime_position,
            position_info: %Torngen.Client.Schema.FactionSlotPositionInfo{
              id: "P" <> slot_index,
              number: crime_position_index
            },
            item_requirement: item_requirement,
            user: nil
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
        slot_index: String.to_integer(slot_index) - 1,
        oc_id: oc_id,
        crime_position: crime_position,
        crime_position_index: crime_position_index,
        user_id: nil,
        user_success_chance: nil,
        user_joined_at: nil
      }
      |> put_item_required(item_requirement)

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

  defp put_item_required(%Tornium.Schema.OrganizedCrimeSlot{} = slot, %{id: item_id, is_available: item_available}) do
    slot
    |> Map.put(:item_required_id, item_id)
    |> Map.put(:item_available, item_available)
  end

  @spec put_delayer(
          slot :: Tornium.Schema.OrganizedCrimeSlot.t(),
          members :: [Torngen.Client.Schema.FactionMember.t()],
          oc_ready :: boolean()
        ) ::
          Tornium.Schema.OrganizedCrimeSlot.t()
  defp put_delayer(%Tornium.Schema.OrganizedCrimeSlot{user_id: user_id} = slot, members, true)
       when is_list(members) and not is_nil(user_id) do
    # We can assume that it is impossible for the member to not be in the members response if they're still in an OC. Otherwise, this indicates an API bug.
    %Torngen.Client.Schema.FactionMember{
      status: %Torngen.Client.Schema.UserStatus{description: user_status_description}
    } = Enum.find(members, fn %Torngen.Client.Schema.FactionMember{id: member_id} -> member_id == user_id end)

    {delayer, delayed_reason} =
      case user_status_description do
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

  @doc """
  Execute the checks in `Tornium.Faction.OC.Check` against an list of Organized Crimes to create a
  `Tornium.Faction.OC.Check.Struct` state that contains the slots or crimes triggering each check.
  """
  @spec check(
          oc_list :: [Tornium.Schema.OrganizedCrime.t()],
          config :: Tornium.Schema.ServerOCConfig.t() | nil,
          oc_checks :: Tornium.Faction.OC.Check.Struct.t() | nil
        ) :: Tornium.Faction.OC.Check.Struct.t()
  def check(oc_list, config, oc_checks \\ nil)

  def check(oc_list, config, oc_checks) when is_list(oc_list) and is_nil(oc_checks) do
    check(oc_list, config, Tornium.Faction.OC.Check.Struct.new())
  end

  def check(
        [%Tornium.Schema.OrganizedCrime{} = oc | remaining_oc],
        %Tornium.Schema.ServerOCConfig{} = config,
        oc_checks
      ) do
    oc_checks =
      oc_checks
      |> Tornium.Faction.OC.Check.check_tools(oc)
      |> Tornium.Faction.OC.Check.check_delayers(oc)
      |> Tornium.Faction.OC.Check.check_extra_range(oc, config)

    check(remaining_oc, config, oc_checks)
  end

  def check([%Tornium.Schema.OrganizedCrime{} = oc | remaining_oc], config, oc_checks) when is_nil(config) do
    # Skip OC checks that require a configuration from a server
    # e.g. extra-range notifications

    oc_checks =
      oc_checks
      |> Tornium.Faction.OC.Check.check_tools(oc)
      |> Tornium.Faction.OC.Check.check_delayers(oc)

    check(remaining_oc, config, oc_checks)
  end

  def check([], _config, oc_checks) do
    oc_checks
  end
end
