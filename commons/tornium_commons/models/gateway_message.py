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

import datetime

from peewee import (
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    SmallIntegerField,
    TextField,
    UUIDField,
)
from playhouse.postgres_ext import ArrayField

from .base_model import BaseModel
from .user import User


class GatewayMessage(BaseModel):
    message_id = UUIDField(primary_key=True)
    message_type = IntegerField(null=False, default=0)

    recipient = TextField(null=True)
    timestamp = DateTimeField(null=False, default=datetime.datetime.utcnow)

    event = TextField(null=True)
    data = TextField(null=True)
