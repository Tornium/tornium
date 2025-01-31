# Copyright (C) 2021-2023 tiksan
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

defmodule Tornium.Schema.Server do
  use Ecto.Schema

  @type t :: %__MODULE__{
          name: String.t(),
          admins: List,
          icon: String.t(),
          factions: List,
          verify_enabled: boolean(),
          auto_verify_enabled: boolean(),
          gateway_verify_enabled: boolean(),
          verify_template: String.t(),
          verified_roles: List,
          exclusion_roles: List,
          faction_verify: Map,
          verify_log_channel: integer(),
          verify_jail_channel: integer(),
          banking_config: Map,
          armory_enabled: boolean(),
          armory_config: Map,
          oc_config: Map
        }

  @primary_key {:sid, :integer, autogenerate: false}
  schema "server" do
    field(:name, :string)
    field(:admins, {:array, :integer})
    field(:icon, :string)

    field(:factions, {:array, :integer})
    # has_many(:factions, Tornium.Schema.Faction)

    field(:verify_enabled, :boolean)
    field(:auto_verify_enabled, :boolean)
    field(:gateway_verify_enabled, :boolean)
    field(:verify_template, :string)
    field(:verified_roles, {:array, :integer})
    field(:exclusion_roles, {:array, :integer})
    field(:faction_verify, :map)
    field(:verify_log_channel, :integer)
    field(:verify_jail_channel, :integer)

    field(:banking_config, :map)

    field(:armory_enabled, :boolean)
    field(:armory_config, :map)

    field(:oc_config, :map)

    has_one(:notifications_config, Tornium.Schema.ServerNotificationsConfig, foreign_key: :server_id, references: :sid)
  end
end
