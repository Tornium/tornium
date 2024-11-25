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
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    UUIDField,
)
from playhouse.postgres_ext import JSONField

from .base_model import BaseModel
from .notification_trigger import NotificationTrigger
from .user import User


class Notification(BaseModel):
    nid = UUIDField(primary_key=True)
    trigger = ForeignKeyField(NotificationTrigger, null=False)
    user = ForeignKeyField(User, null=False)

    resource_id = IntegerField(default=None, null=True)
    one_shot = BooleanField(default=True, null=False)

    next_execution = DateTimeField(default=None, null=True)

    error = CharField(default=None, null=True)
    previous_state = JSONField(default={}, null=False)
