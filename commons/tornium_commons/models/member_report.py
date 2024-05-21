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
    BigIntegerField,
    DateTimeField,
    IntegerField,
    SmallIntegerField,
    TextField,
    UUIDField,
)
from playhouse.postgres_ext import ArrayField

from .base_model import BaseModel


class MemberReport(BaseModel):
    rid = UUIDField(primary_key=True)
    created_at = DateTimeField()
    last_updated = DateTimeField()
    requested_by_user = IntegerField(null=True)
    requested_by_faction = IntegerField(null=True)
    requested_data = ArrayField(TextField)
    status = SmallIntegerField()

    # Report Status
    # 0: Not started
    # 1: In progress
    # 2: Completed
    # 999: Error

    faction_tid = IntegerField()
    start_timestamp = DateTimeField()
    end_timestamp = DateTimeField()

    # PostgreSQL currently does not support arrays of foreign keys
    # Reference: https://stackoverflow.com/questions/41054507/postgresql-array-of-elements-that-each-are-a-foreign-key
    start_ps = ArrayField(BigIntegerField, index=False, default=[])
    end_ps = ArrayField(BigIntegerField, index=False, default=[])
