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
  use Ecto.Schema

  @type t :: %__MODULE__{
          id: Ecto.UUID.t(),
          oc: Tornium.Schema.OrganizedCrime.t(),
          slot_index: integer(),
          crime_position: String.t(),
          user_id: integer() | nil,
          user: Tornium.Schema.User.t() | nil,
          user_success_chance: integer() | nil,
          item_required: Tornium.Schema.Item.t() | nil,
          item_available: boolean() | nil,
          delayer: boolean() | nil,
          delayed_reason: String.t(),
          sent_tool_notification: boolean()
        }

  @primary_key {:id, Ecto.UUID, autogenerate: true}
  schema "organized_crime_slot" do
    belongs_to(:oc, Tornium.Schema.OrganizedCrime, references: :oc_id)
    field(:slot_index, :integer)

    field(:crime_position, :string)
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    field(:user_success_chance, :integer)

    belongs_to(:item_required, Tornium.Schema.Item, references: :tid)
    field(:item_available, :boolean)

    field(:delayer, :boolean)
    field(:delayed_reason, :string)

    field(:sent_tool_notification, :boolean)
  end

  @spec map(entries :: [Tornium.Schema.OrganizedCrimeSlot.t()]) :: list(map())
  def map(entries) do
    entries
    |> Enum.with_index()
    |> Enum.map(fn {
                     %Tornium.Schema.OrganizedCrimeSlot{
                       id: id,
                       oc_id: oc_id,
                       crime_position: crime_position,
                       user_id: user_id,
                       user_success_chance: user_success_chance,
                       item_required_id: item_required_id,
                       item_available: item_available,
                       delayer: delayer,
                       delayed_reason: delayed_reason,
                       sent_tool_notification: sent_tool_notification
                     },
                     index
                   }
                   when is_integer(index) ->
      %{
        id: id || Ecto.UUID.generate(),
        oc_id: oc_id,
        slot_index: index,
        crime_position: crime_position,
        user_id: user_id,
        user_success_chance: user_success_chance,
        item_required_id: item_required_id,
        item_available: item_available || false,
        delayer: delayer || false,
        delayed_reason: delayed_reason,
        sent_tool_notification: sent_tool_notification || false
      }
    end)
  end

  @spec upsert_all(entries :: [t()]) :: [t()]
  def upsert_all([%Tornium.Schema.OrganizedCrimeSlot{} | _] = entries) when is_list(entries) do
    # The entries are still in the format of the schema and needs to be remapped first
    entries
    |> Enum.map(&map/1)
    |> upsert_all()
  end

  def upsert_all([entry | _] = entries) when is_list(entries) and is_map(entry) do
    # WARNING: Test logic for when member joins a slot and leaves the slot
    # TODO: clear old data (such as `sent_tool_notification`) when a member leaves a slot or a different member joins the slot

    # The schema entries have already been remapped
    {_, returned_slot_entries} =
      Repo.insert_all(Tornium.Schema.OrganizedCrimeSlot, entries,
        on_conflict: {:replace_all_except, [:id]},
        conflict_target: [:oc_id, :slot_index, :user_id],
        returning: true
      )

    returned_slot_entries
  end
end
