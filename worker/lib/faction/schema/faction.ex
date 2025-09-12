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

defmodule Tornium.Schema.Faction do
  use Ecto.Schema

  @type t :: %__MODULE__{
          tid: integer(),
          name: String.t(),
          tag: String.t(),
          respect: integer(),
          capacity: integer(),
          leader: Tornium.Schema.User.t(),
          coleader: Tornium.Schema.User.t(),
          guild: Tornium.Schema.Server.t(),
          stats_db_enabled: boolean(),
          stats_db_global: boolean(),
          last_members: DateTime.t(),
          last_attacks: DateTime.t(),
          has_migrated_oc: boolean()
        }

  @primary_key {:tid, :integer, autogenerate: false}
  schema "faction" do
    field(:name, :string)
    field(:tag, :string)
    field(:respect, :integer)
    field(:capacity, :integer)
    belongs_to(:leader, Tornium.Schema.User, references: :tid)
    belongs_to(:coleader, Tornium.Schema.User, references: :tid)

    belongs_to(:guild, Tornium.Schema.Server, references: :sid)

    field(:stats_db_enabled, :boolean)
    field(:stats_db_global, :boolean)

    field(:last_members, :utc_datetime_usec)
    field(:last_attacks, :utc_datetime_usec)
    field(:has_migrated_oc, :boolean)
  end
end
