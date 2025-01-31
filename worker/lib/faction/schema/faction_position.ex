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

defmodule Tornium.Schema.FactionPosition do
  use Ecto.Schema

  @type t :: %__MODULE__{
          pid: Ecto.UUID.t(),
          name: String.t(),
          faction_tid: integer(),
          default: boolean(),
          use_medical_item: boolean(),
          use_booster_item: boolean(),
          use_drug_item: boolean(),
          use_energy_refill: boolean(),
          use_nerve_refill: boolean(),
          loan_temporary_item: boolean(),
          loan_weapon_armory: boolean(),
          retrieve_loaned_armory: boolean(),
          plan_init_oc: boolean(),
          access_fac_api: boolean(),
          give_item: boolean(),
          give_money: boolean(),
          give_points: boolean(),
          manage_forums: boolean(),
          manage_applications: boolean(),
          kick_members: boolean(),
          adjust_balances: boolean(),
          manage_wars: boolean(),
          manage_upgrades: boolean(),
          send_newsletters: boolean(),
          change_announcement: boolean(),
          change_description: boolean()
        }

  @primary_key {:pid, Ecto.UUID, autogenerate: true}
  schema "factionposition" do
    field(:name, :string)
    field(:faction_tid, :integer)

    field(:default, :boolean)

    field(:use_medical_item, :boolean)
    field(:use_booster_item, :boolean)
    field(:use_drug_item, :boolean)
    field(:use_energy_refill, :boolean)
    field(:use_nerve_refill, :boolean)
    field(:loan_temporary_item, :boolean)
    field(:loan_weapon_armory, :boolean)
    field(:retrieve_loaned_armory, :boolean)
    field(:plan_init_oc, :boolean)
    field(:access_fac_api, :boolean)
    field(:give_item, :boolean)
    field(:give_money, :boolean)
    field(:give_points, :boolean)
    field(:manage_forums, :boolean)
    field(:manage_applications, :boolean)
    field(:kick_members, :boolean)
    field(:adjust_balances, :boolean)
    field(:manage_wars, :boolean)
    field(:manage_upgrades, :boolean)
    field(:send_newsletters, :boolean)
    field(:change_announcement, :boolean)
    field(:change_description, :boolean)
  end
end
