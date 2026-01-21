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

from peewee import CharField, DateTimeField, ForeignKeyField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel
from .extra_fields import INETField
from .user import User


class GatewayToken(BaseModel):
    class Meta:
        table_name = "gateway_token"

    guid = UUIDField(primary_key=True)
    user = ForeignKeyField(User, null=False)
    token = CharField(max_length=64, null=False)

    created_at = DateTimeField(null=False, default=datetime.datetime.utcnow)
    created_ip = INETField(null=False)
    expires_at = DateTimeField(null=False)
