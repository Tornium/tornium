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

defmodule Tornium.Schema.OrganizedCrimeSlot do
  alias Tornium.Repo
  import Ecto.Query
  use Ecto.Schema

  @type t :: %__MODULE__{
          id: Ecto.UUID.t(),
          oc_id: non_neg_integer(),
          oc: Tornium.Schema.OrganizedCrime.t(),
          slot_index: integer(),
          crime_position: String.t(),
          crime_position_index: integer(),
          user_id: integer() | nil,
          user: Tornium.Schema.User.t() | nil,
          user_success_chance: integer() | nil,
          user_joined_at: DateTime.t() | nil,
          item_required_id: non_neg_integer() | nil,
          item_required: Tornium.Schema.Item.t() | nil,
          item_available: boolean() | nil,
          delayer: boolean(),
          delayed_reason: String.t() | nil,
          sent_tool_notification: boolean(),
          sent_delayer_notification: boolean(),
          sent_extra_range_notification: boolean()
        }

  @primary_key {:id, Ecto.UUID, autogenerate: true}
  schema "organized_crime_slot" do
    belongs_to(:oc, Tornium.Schema.OrganizedCrime, references: :oc_id)
    field(:slot_index, :integer)

    field(:crime_position, :string)
    field(:crime_position_index, :integer)
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    field(:user_success_chance, :integer)
    field(:user_joined_at, :utc_datetime)

    belongs_to(:item_required, Tornium.Schema.Item, references: :tid)
    field(:item_available, :boolean)

    field(:delayer, :boolean)
    field(:delayed_reason, :string)

    field(:sent_tool_notification, :boolean)
    field(:sent_delayer_notification, :boolean)
    field(:sent_extra_range_notification, :boolean)
  end

  @spec upsert_all(entries :: [t()]) :: [t()]
  def upsert_all([%Tornium.Schema.OrganizedCrimeSlot{} | _] = entries) when is_list(entries) do
    # [Ecto.Schema] -> [map()] transformation comes from https://github.com/elixir-ecto/ecto/issues/1167#issuecomment-186894460
    # NOTE: need to remove internal ecto data, associations, and data not originating from the Torn API before upserting

    delayers =
      entries
      |> Enum.reduce(%{}, fn %Tornium.Schema.OrganizedCrimeSlot{
                               oc_id: oc_id,
                               slot_index: slot_index,
                               delayer: delayer,
                               delayed_reason: delayed_reason
                             },
                             acc ->
        case delayer do
          _ when is_nil(delayer) or delayer == false -> acc
          _ -> Map.put(acc, {oc_id, slot_index}, %{delayer: delayer, delayed_reason: delayed_reason})
        end
      end)

    entries
    |> Enum.map(&Map.from_struct/1)
    |> Enum.map(
      &Map.drop(&1, [
        :__struct__,
        :__meta__,
        :user,
        :item_required,
        :oc,
        :delayer,
        :delayed_reason,
        :sent_tool_notification,
        :sent_delayer_notification,
        :sent_extra_range_notification
      ])
    )
    |> Enum.map(fn %{} = slot -> Map.update!(slot, :id, fn id -> id || Ecto.UUID.generate() end) end)
    |> upsert_all(delayers)
  end

  def upsert_all([] = _entries) do
    # Fallback
    []
  end

  def upsert_all([entry | _] = entries, delayers) when is_map(entry) and is_map(delayers) do
    # Find all slots where the user ID for the slot does not match the user ID in the API response.
    # Indicates that the user left the slot.
    # The slot should be deleted to avoid bad/old data from polluting the current user of the slot.
    potential_deletions = Enum.reject(entries, &is_nil(&1.user_id))

    if potential_deletions != [] do
      # Source: https://geekmonkey.org/updating-multiple-records-with-different-values-in-ecto-repo-update_all/
      Tornium.Schema.OrganizedCrimeSlot
      |> join(
        :inner,
        [s],
        data in fragment(
          "SELECT * FROM unnest(?::int[], ?::int[], ?::int[]) AS data(oc_id, slot_index, user_id)",
          ^Enum.map(potential_deletions, & &1.oc_id),
          ^Enum.map(potential_deletions, & &1.slot_index),
          ^Enum.map(potential_deletions, & &1.user_id)
        ),
        on: s.oc_id == data.oc_id and s.slot_index == data.slot_index
      )
      |> where([s, data], not is_nil(s.user_id) and s.user_id != data.user_id)
      |> Repo.delete_all()
    end

    # NOTE: Don't replace certain data that doesn't originate from the Torn API as the data will not exist until checks run
    # The data should be used if the slot does not already exist though
    # TODO: Make the query replace only certain targets instead of all except
    {_, returned_slot_entries} =
      Repo.insert_all(Tornium.Schema.OrganizedCrimeSlot, entries,
        on_conflict:
          {:replace_all_except,
           [
             :id,
             :oc_id,
             :slot_index,
             :delayer,
             :delayer_reason,
             :sent_tool_notification,
             :sent_delayer_notification,
             :sent_extra_range_notification
           ]},
        conflict_target: [:oc_id, :slot_index],
        returning: true
      )

    returned_slot_entries
    |> Enum.map(fn %Tornium.Schema.OrganizedCrimeSlot{oc_id: oc_id, slot_index: slot_index, delayer: delayer} = slot ->
      cond do
        delayer == true ->
          slot

        not is_nil(Map.get(delayers, {oc_id, slot_index})) ->
          %{delayer: delayer_new, delayed_reason: delayed_reason_new} =
            Map.get(delayers, {oc_id, slot_index})

          Tornium.Schema.OrganizedCrimeSlot
          |> where(
            [s],
            s.oc_id == ^oc_id and s.slot_index == ^slot_index and s.delayer == false and is_nil(s.delayed_reason)
          )
          |> update([s], set: [delayer: ^delayer_new, delayed_reason: ^delayed_reason_new])
          |> Repo.update_all([])

          slot
          |> Map.put(:delayer, delayer_new)
          |> Map.put(:delayed_reason, delayed_reason_new)

        true ->
          slot
      end
    end)
  end

  def upsert_all([] = _entries, _delayers) do
    # Fallback
    []
  end

  @doc ~S"""
  Update the sent state of slots for each checked feature from the state of `Tornium.Faction.OC.Check.Struct`.
  """
  @spec update_sent_state(check_state :: Tornium.Faction.OC.Check.Struct.t()) :: nil
  def update_sent_state(
        %Tornium.Faction.OC.Check.Struct{missing_tools: missing_tools, delayers: delayers, extra_range: extra_range} =
          _check_state
      )
      when Kernel.length(missing_tools) == 0 and Kernel.length(delayers) == 0 and Kernel.length(extra_range) == 0 do
    nil
  end

  def update_sent_state(%Tornium.Faction.OC.Check.Struct{} = check_state) do
    update_tool_state(check_state)
    update_delayer_state(check_state)
    update_extra_range_state(check_state)

    nil
  end

  @spec update_tool_state(check_state :: Tornium.Faction.OC.Check.Struct.t()) :: nil
  defp update_tool_state(%Tornium.Faction.OC.Check.Struct{missing_tools: missing_tools} = _check_state)
       when Kernel.length(missing_tools) != 0 do
    missing_tools_ids = get_ids(missing_tools)

    Tornium.Schema.OrganizedCrimeSlot
    |> where([s], s.id in ^missing_tools_ids)
    |> update(set: [sent_tool_notification: true])
    |> Repo.update_all([])

    nil
  end

  defp update_tool_state(_check_state) do
    nil
  end

  @spec update_delayer_state(check_state :: Tornium.Faction.OC.Check.Struct.t()) :: nil
  defp update_delayer_state(%Tornium.Faction.OC.Check.Struct{delayers: delayers} = _check_state)
       when Kernel.length(delayers) != 0 do
    delayers_ids = get_ids(delayers)

    Tornium.Schema.OrganizedCrimeSlot
    |> where([s], s.id in ^delayers_ids)
    |> update(set: [sent_delayer_notification: true])
    |> Repo.update_all([])

    nil
  end

  defp update_delayer_state(_check_state) do
    nil
  end

  @spec update_extra_range_state(check_state :: Tornium.Faction.OC.Check.Struct.t()) :: nil
  defp update_extra_range_state(%Tornium.Faction.OC.Check.Struct{extra_range: extra_range} = _check_state)
       when Kernel.length(extra_range) != 0 do
    extra_range_ids = get_ids(extra_range)

    Tornium.Schema.OrganizedCrimeSlot
    |> where([s], s.id in ^extra_range_ids)
    |> update(set: [sent_extra_range_notification: true])
    |> Repo.update_all([])

    nil
  end

  defp update_extra_range_state(_check_state) do
    nil
  end

  @spec get_ids(list_slots :: [Tornium.Schema.OrganizedCrimeSlot.t()]) :: [Ecto.UUID.t() | String.t()]
  defp get_ids(list_slots) do
    # TODO: make this function look better
    Enum.map(list_slots, fn %Tornium.Schema.OrganizedCrimeSlot{id: id} -> id end)
  end
end
