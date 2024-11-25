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

from peewee import BooleanField, CharField, ForeignKeyField, UUIDField, IntegerField
from playhouse.postgres_ext import ArrayField

from .base_model import BaseModel
from .user import User


class NotificationTrigger(BaseModel):
    class Meta:
        table_name = "notification_trigger"

    tid = UUIDField(primary_key=True)
    name = CharField(null=False)
    description = CharField(null=False, default="")
    owner = ForeignKeyField(User, null=False)

    resource = CharField(null=False, choices=["user", "faction", "company", "torn", "faction_v2"])
    selections = ArrayField(CharField, default=[], index=False)
    code = CharField(null=False)

    message_type = IntegerField(null=False, choices=[0, 1])
    message_template = CharField(null=False)

    public = BooleanField(default=False, null=False)
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
            "public": self.public,
            "official": self.official,
        }
