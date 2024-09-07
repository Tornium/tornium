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

  @primary_key {:sid, :integer, autogenerate: false}
  schema "server" do
    field(:name, :string)
    field(:admins, {:array, :integer})
    field(:icon, :string)

    # field(:factions, {:array, :integer})
    has_many(:factions, Tornium.Schema.Faction)

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

    field(:assist_channel, :integer)
    field(:assist_factions, {:array, :integer})
    field(:assist_smoker_roles, {:array, :integer})
    field(:assist_tear_roles, {:array, :integer})
    field(:assist_l0_roles, {:array, :integer})
    field(:assist_l1_roles, {:array, :integer})
    field(:assist_l2_roles, {:array, :integer})
    field(:assist_l3_roles, {:array, :integer})

    field(:oc_config, :map)
  end
end
