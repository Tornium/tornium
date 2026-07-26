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

from peewee import BooleanField, DateTimeField, TextField, CharField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel


class TornEvent(BaseModel):
    class Meta:
        table_name = "torn_event"

    guid = UUIDField(primary_key=True)

    title = CharField(null=False)
    description = TextField(null=False)
    type = CharField(null=False)
    # TODO: make `type` an enum
    # See https://github.com/coleifer/peewee/issues/630

    start_timestamp = DateTimeField(null=False)
    end_timestamp = DateTimeField(null=False)
    configurable = BooleanField(default=False, null=False)
