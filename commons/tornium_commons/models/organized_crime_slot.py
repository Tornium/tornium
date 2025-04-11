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

from peewee import (
    BooleanField,
    CharField,
    ForeignKeyField,
    SmallIntegerField,
    UUIDField,
)

from .base_model import BaseModel
from .item import Item
from .organized_crime_new import OrganizedCrimeNew
from .user import User


class OrganizedCrimeSlot(BaseModel):
    class Meta:
        table_name = "organized_crime_slot"

    id = UUIDField(primary_key=True)
    oc = ForeignKeyField(OrganizedCrimeNew, null=False)

    crime_position = CharField(null=False)
    user = ForeignKeyField(User, null=False)
    user_success_chance = SmallIntegerField(default=None, null=True)

    item_required = ForeignKeyField(Item, default=None, null=True)
    item_available = BooleanField(default=None, null=True)
