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

import enum

from peewee import (
    BigIntegerField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
    UUIDField,
)
from playhouse.postgres_ext import ArrayField

from .base_model import BaseModel
from .server import Server
from .user import User


class VerificationLogResult(enum.Enum):
    UNVERIFIED = "unverified"
    DISCORD_PERMISSION = "discord_permission"
    NO_API_KEY = "no_api_key"
    CONFIG = "config"
    TORN_API = "torn_api"
    DISCORD_API = "discord_api"


class VerificationLog(BaseModel):
    guid = UUIDField(primary_key=True)
    server = ForeignKeyField(Server, null=False)
    discord_id = BigIntegerField(default=None, null=True)
    user = ForeignKeyField(User, default=None, null=True)

    old_nickname = TextField(default=None, null=True)
    new_nickname = TextField(default=None, null=True)
    roles_added = ArrayField(BigIntegerField, default=[], null=False)
    roles_removed = ArrayField(BigIntegerField, default=[], null=False)

    # TODO: make `error_type` an enum
    # See https://github.com/coleifer/peewee/issues/630
    error_type = TextField(default=None, null=True)
    error_code = IntegerField(default=None, null=True)
    error_message = TextField(default=None, null=True)

    timestamp = DateTimeField(null=False)

    class Meta:
        table_name = "verification_log"

    def to_dict(self) -> dict:
        from ..formatters import timestamp

        return {"guid": self.guid, "timestamp": timestamp(self.timestamp), "server_id": self.server_id}
