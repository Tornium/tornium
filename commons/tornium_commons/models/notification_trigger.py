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
    DateTimeField,
    ForeignKeyField,
    TextField,
    UUIDField,
)
from playhouse.postgres_ext import ArrayField, JSONField

from .base_model import BaseModel
from .user import User


class NotificationTrigger(BaseModel):
    class Meta:
        table_name = "notification_trigger"

    tid = UUIDField(primary_key=True)
    name = CharField(null=False)
    description = TextField(null=False, default="")
    owner = ForeignKeyField(User, null=False)

    cron = CharField(default="* * * * *", null=False)
    next_execution = DateTimeField(default=None, null=True)
    resource = CharField(null=False, choices=["user", "faction", "company", "torn", "faction_v2"])
    selections = ArrayField(CharField, default=[], index=False)
    code = TextField(null=False)
    parameters = JSONField(default={}, null=False)

    message_type = CharField(null=False, choices=["update", "send"])
    message_template = TextField(null=False)

    restricted_data = BooleanField(default=False, null=False)
    official = BooleanField(default=False, null=False)

    def as_dict(self):
        return {
            "tid": self.tid,
            "name": self.name,
            "description": self.description,
            "owner": self.owner_id,
            "resource": self.resource,
            "selections": self.selections,
            "code": self.code,
            "restricted_data": self.restricted_data,
            "official": self.official,
        }
