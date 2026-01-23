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

defmodule Tornium.Schema.OrganizedCrimeCPR do
  @moduledoc """
  Users' CPRs in slots for different OCs.

  ## Fields
  - `:guid` - Unique internal identifier
  - `:user` - User the CPR belongs to
  - `:oc_name` - Name of the OC (e.g. `Break the Bank`)
  - `:oc_position` - Position in the specified OC name (e.g. `Muscle`)
  - `:cpr` - Success chance in the specified position in the specified OC name
  - `:updated_at` - The last time the CPR was updated for this user + OC + position
  """

  use Ecto.Schema
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          user_id: integer(),
          user: Tornium.Schema.User.t(),
          oc_name: String.t(),
          oc_position: String.t(),
          cpr: integer(),
          updated_at: DateTime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_cpr" do
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    field(:oc_name, :string)
    field(:oc_position, :string)
    field(:cpr, :integer)
    field(:updated_at, :utc_datetime)
  end

  @spec upsert_all(entries :: [t()]) :: :ok
  def upsert_all([%__MODULE__{} | _] = entries) do
    entries
    |> Enum.chunk_every(200)
    |> Enum.each(&do_upsert_all/1)

    :ok
  end

  def upsert_all(_entries) do
    # Fallback for API error
    :ok
  end

  defp do_upsert_all([%__MODULE__{} | _] = entries) do
    query = """
    INSERT INTO organized_crime_cpr
      (guid, user_id, oc_name, oc_position, cpr, updated_at)
    SELECT *
    FROM unnest($1::uuid[], $2::integer[], $3::text[], $4::text[], $5::integer[], $6::timestamp[])
      AS data(guid, user_id, oc_name, oc_position, cpr, updated_at)
    ON CONFLICT (user_id, oc_name, oc_position)
    DO UPDATE SET cpr = EXCLUDED.cpr, updated_at = EXCLUDED.updated_at
    """

    {:ok, _} =
      Repo.query(query, [
        Enum.map(entries, &Ecto.UUID.dump!(&1.guid)),
        Enum.map(entries, & &1.user_id),
        Enum.map(entries, & &1.oc_name),
        Enum.map(entries, & &1.oc_position),
        Enum.map(entries, & &1.cpr),
        Enum.map(entries, & &1.updated_at)
      ])

    :ok
  end
end
