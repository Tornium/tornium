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

from peewee import (
    BooleanField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    SmallIntegerField,
)
from playhouse.postgres_ext import ArrayField

from .base_model import BaseModel
from .user import User


class OrganizedCrime(BaseModel):
    faction_tid = IntegerField(index=True)
    oc_id = IntegerField(primary_key=True)
    crime_id = SmallIntegerField()
    participants = ArrayField(IntegerField, index=False)  # Array of participant user IDs
    time_started = DateTimeField(null=True)
    time_ready = DateTimeField(null=True)
    time_completed = DateTimeField(null=True)
    planned_by = ForeignKeyField(User, null=True)
    initiated_by = ForeignKeyField(User, null=True)
    money_gain = IntegerField(null=True)
    respect_gain = IntegerField(null=True)
    delayers = ArrayField(IntegerField, index=False)  # Array of delayer user IDs
    notified = BooleanField(default=False)
    initiated = BooleanField(default=False)
