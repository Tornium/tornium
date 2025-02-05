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

defmodule Tornium.Schema.User do
  use Ecto.Schema

  @type t :: %__MODULE__{
          tid: integer(),
          name: String.t(),
          level: integer(),
          discord_id: integer(),
          battlescore: float(),
          strength: integer(),
          defense: integer(),
          speed: integer(),
          dexterity: integer(),
          faction: Tornium.Schema.Faction.t(),
          faction_aa: boolean(),
          faction_position: Tornium.Schema.FactionPosition.t(),
          status: String.t(),
          last_action: DateTime.t(),
          last_refresh: DateTime.t(),
          last_attacks: DateTime.t(),
          battlescore_update: DateTime.t(),
          security: integer(),
          otp_secret: String.t(),
          otp_backups: List
        }

  @primary_key {:tid, :integer, autogenerate: false}
  schema "user" do
    field(:name, :string)
    field(:level, :integer)
    field(:discord_id, :integer)
    # has_one(:personal_stats, Tornium.Schema.PersonalStats)

    field(:battlescore, :float)
    field(:strength, :integer)
    field(:defense, :integer)
    field(:speed, :integer)
    field(:dexterity, :integer)

    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    field(:faction_aa, :boolean)
    belongs_to(:faction_position, Tornium.Schema.FactionPosition, references: :pid, type: :binary_id)

    field(:status, :string)
    field(:last_action, :utc_datetime)

    field(:last_refresh, :utc_datetime_usec)
    field(:last_attacks, :utc_datetime_usec)
    field(:battlescore_update, :utc_datetime_usec)

    field(:security, :integer)
    field(:otp_secret, :string)
    field(:otp_backups, {:array, :string})
  end
end
