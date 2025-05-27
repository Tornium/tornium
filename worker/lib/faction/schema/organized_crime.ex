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

defmodule Tornium.Schema.OrganizedCrime do
  alias Tornium.Repo
  use Ecto.Schema

  @type t :: %__MODULE__{
          oc_id: integer(),
          oc_name: String.t(),
          oc_difficulty: integer(),
          faction: Tornium.Schema.Faction.t(),
          status: :recruiting | :planning | :successful | :failure | :expired,
          created_at: DateTime.t(),
          planning_started_at: DateTime.t() | nil,
          ready_at: DateTime.t() | nil,
          expires_at: DateTime.t(),
          executed_at: DateTime.t() | nil,
          slots: [Tornium.Schema.OrganizedCrimeSlot.t()]
        }

  @primary_key {:oc_id, :integer, autogenerate: false}
  schema "organized_crime_new" do
    field(:oc_name, :string)
    field(:oc_difficulty, :integer)

    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    field(:status, Ecto.Enum, values: [:recruiting, :planning, :successful, :failure, :expired])

    field(:created_at, :utc_datetime)
    field(:planning_started_at, :utc_datetime)
    field(:ready_at, :utc_datetime)
    field(:expires_at, :utc_datetime)
    field(:executed_at, :utc_datetime)

    has_many(:slots, Tornium.Schema.OrganizedCrimeSlot, foreign_key: :oc_id)
  end

  @spec upsert_all(entries :: [t()]) :: [t()]
  def upsert_all(entries) when is_list(entries) do
    # TODO: Check the type of the head of the list
    {_, returned_entries} =
      entries
      |> map()
      |> (&Repo.insert_all(Tornium.Schema.OrganizedCrime, &1,
            on_conflict: :replace_all,
            conflict_target: [:oc_id],
            returning: true
          )).()

    slot_users =
      entries
      |> Enum.flat_map(fn %Tornium.Schema.OrganizedCrime{slots: slots} -> slots end)
      |> Enum.map(fn %Tornium.Schema.OrganizedCrimeSlot{user_id: user_id} -> user_id end)
      |> Enum.reject(&is_nil/1)
      |> Enum.uniq()
      |> Enum.map(
        &%{
          tid: &1
        }
      )

    Repo.insert_all(Tornium.Schema.User, slot_users, on_conflict: :nothing, conflict_target: [:tid])

    returned_slot_entries =
      entries
      |> Enum.flat_map(fn %Tornium.Schema.OrganizedCrime{slots: slots} ->
        slots
      end)
      |> Tornium.Schema.OrganizedCrimeSlot.upsert_all()
      |> Enum.group_by(& &1.oc_id)

    Enum.map(returned_entries, fn %Tornium.Schema.OrganizedCrime{oc_id: oc_id} = oc ->
      # TODO: Determine a better way to implement this
      # Maybe use something similar to https://hexdocs.pm/ecto/Ecto.Repo.html#c:load/2
      Map.replace(oc, :slots, returned_slot_entries[oc_id])
    end)
  end

  @spec map(entries :: [t()]) :: list(map())
  def map(entries) when is_list(entries) do
    Enum.map(
      entries,
      fn %Tornium.Schema.OrganizedCrime{
           oc_id: oc_id,
           oc_name: oc_name,
           oc_difficulty: oc_difficulty,
           faction_id: faction_id,
           status: status,
           created_at: created_at,
           planning_started_at: planning_started_at,
           ready_at: ready_at,
           expires_at: expires_at,
           executed_at: executed_at
         } ->
        %{
          oc_id: oc_id,
          oc_name: oc_name,
          oc_difficulty: oc_difficulty,
          faction_id: faction_id,
          status: status,
          created_at: created_at,
          planning_started_at: planning_started_at,
          ready_at: ready_at,
          expires_at: expires_at,
          executed_at: executed_at
        }
      end
    )
  end
end
