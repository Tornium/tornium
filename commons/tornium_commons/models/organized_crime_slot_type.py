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

from peewee import BooleanField, CharField, ForeignKeyField, SmallIntegerField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel
from .item import Item
from .organized_crime_type import OrganizedCrimeType


class OrganizedCrimeSlotType(BaseModel):
    class Meta:
        table_name = "organized_crime_slot_type"

    guid = UUIDField(primary_key=True)

    oc_type = ForeignKeyField(OrganizedCrimeType, null=False)
    name = CharField(null=False)
    number = SmallIntegerField(null=False)
    index = SmallIntegerField(null=False)

    required_item = ForeignKeyField(Item, default=None, null=True)
    required_item_consumed = BooleanField(default=None, null=True)
