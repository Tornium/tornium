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

import typing
from functools import lru_cache

from peewee import (
    BigIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    SmallIntegerField,
)

from .base_model import BaseModel
from .faction import Faction


class OrganizedCrimeNew(BaseModel):
    class Meta:
        table_name = "organized_crime_new"

    oc_id = BigIntegerField(primary_key=True)
    oc_name = CharField(null=False)
    oc_difficulty = SmallIntegerField(null=False)

    faction = ForeignKeyField(Faction, null=False)

    status = CharField(null=False)

    created_at = DateTimeField(null=False)
    planning_started_at = DateTimeField(default=None, null=True)
    ready_at = DateTimeField(default=None, null=True)
    expires_at = DateTimeField(default=None, null=True)
    executed_at = DateTimeField(default=None, null=True)

    @classmethod
    @lru_cache
    def oc_names(cls) -> typing.List[str]:
        return [crime.oc_name for crime in OrganizedCrimeNew.select().distinct(OrganizedCrimeNew.oc_name)]
