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

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          user_id: integer(),
          user: Tornium.Schema.User.t(),
          oc_name: String.t(),
          oc_position: String.t(),
          cpr: integer(),
          updated_at: DateTime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: false}
  schema "organized_crime_cpr" do
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    field(:oc_name, :string)
    field(:oc_position, :string)
    field(:cpr, :integer)
    field(:updated_at, :utc_datetime_usec)
  end
end
