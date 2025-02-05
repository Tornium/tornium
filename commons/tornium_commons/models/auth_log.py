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
import enum

from peewee import DateTimeField, ForeignKeyField, IntegerField, TextField

from .base_model import BaseModel
from .extra_fields import IPAddressField
from .user import User


class AuthAction(enum.Enum):
    LOGIN_FAILED = 0

    LOGIN_TORN_API_SUCCESS = 1
    LOGIN_TORN_API_FAILED = 2
    LOGIN_TORN_API_PARTIAL = 3  # User has TOTP enabled

    LOGIN_DISCORD_SUCCESS = 11
    LOGIN_DISCORD_FAILED = 12
    LOGIN_DISCORD_PARTIAL = 13  # User has TOTP enabled

    LOGIN_TOTP_SUCCESS = 21
    LOGIN_TOTP_FAILED = 22

    LOGOUT_SUCESS = 31
    LOGOUT_FAILED = 32


class AuthLog(BaseModel):
    user = ForeignKeyField(User, null=True)
    timestamp = DateTimeField(null=False, default=datetime.datetime.utcnow)
    ip = IPAddressField(null=True)
    action = IntegerField(null=False)

    # Value used to login in
    # Can be a Discord ID or Torn API key
    login_key = TextField(null=True)
    details = TextField(null=True)
