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
    BooleanField,
    CharField,
    ForeignKeyField,
    IntegerField,
    UUIDField,
)
from playhouse.postgres_ext import JSONField

from .base_model import BaseModel
from .notification_trigger import NotificationTrigger
from .server import Server
from .user import User


class Notification(BaseModel):
    nid = UUIDField(primary_key=True)
    trigger = ForeignKeyField(NotificationTrigger, null=False)
    user = ForeignKeyField(User, null=False)  # User that created the notification
    enabled = BooleanField(default=True, null=False)

    server = ForeignKeyField(Server, null=True)
    channel_id = BigIntegerField(null=True)
    message_id = BigIntegerField(default=None, null=True)  # Message for auto-updating message

    resource_id = IntegerField(default=None, null=True)
    one_shot = BooleanField(default=True, null=False)
    parameters = JSONField(default={}, null=False)

    error = CharField(default=None, null=True)
    previous_state = JSONField(default={}, null=False)

    def as_dict(self):
        return {
            "nid": self.nid,
            "trigger": self.trigger.as_dict(),
            "user": self.user_id,
            "server": self.server_id,
            "channel_id": self.channel_id,
            "resource_id": self.resource_id,
            "one_shot": self.one_shot,
        }
