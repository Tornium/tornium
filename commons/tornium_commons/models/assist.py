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
    BigIntegerField,
    DateTimeField,
    ForeignKeyField,
    SmallIntegerField,
    TextField,
    UUIDField,
)
from playhouse.postgres_ext import ArrayField

from .base_model import BaseModel
from .user import User


class AssistMessage(BaseModel):
    message_id = BigIntegerField(primary_key=True)
    channel_id = BigIntegerField(null=False)
    celery_delete_id = TextField()


class Assist(BaseModel):
    guid = UUIDField(primary_key=True)
    time_requested = DateTimeField(null=False, default=datetime.datetime.utcnow())

    target = ForeignKeyField(User)
    requester = ForeignKeyField(User)

    remaining_smokes = SmallIntegerField(default=0)
    remaining_tears = SmallIntegerField(default=0)
    remaining_heavies = SmallIntegerField(default=0)

    # Each element is a primary key of AssistMessage
    sent_messages = ArrayField(BigIntegerField, index=False, default=[], null=False)
