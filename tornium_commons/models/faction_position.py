# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from peewee import BooleanField, CharField, IntegerField, UUIDField

from .base_model import BaseModel


class FactionPosition(BaseModel):
    pid = UUIDField(primary_key=True)
    name = CharField()
    faction_tid = IntegerField()

    default = BooleanField(default=False)

    # Permissions
    use_medical_item = BooleanField(default=False)
    use_booster_item = BooleanField(default=False)
    use_drug_item = BooleanField(default=False)
    use_energy_refill = BooleanField(default=False)
    use_nerve_refill = BooleanField(default=False)
    loan_temporary_item = BooleanField(default=False)
    loan_weapon_armory = BooleanField(default=False)
    retrieve_loaned_armory = BooleanField(default=False)
    plan_init_oc = BooleanField(default=False)
    access_fac_api = BooleanField(default=False)
    give_item = BooleanField(default=False)
    give_money = BooleanField(default=False)
    give_points = BooleanField(default=False)
    manage_forums = BooleanField(default=False)
    manage_applications = BooleanField(default=False)
    kick_members = BooleanField(default=False)
    adjust_balances = BooleanField(default=False)
    manage_wars = BooleanField(default=False)
    manage_upgrades = BooleanField(default=False)
    send_newsletters = BooleanField(default=False)
    change_announcement = BooleanField(default=False)
    change_description = BooleanField(default=False)
