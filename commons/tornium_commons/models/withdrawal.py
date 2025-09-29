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
    BooleanField,
    DateTimeField,
    IntegerField,
    SmallIntegerField,
    UUIDField,
)

from .base_model import BaseModel


class Withdrawal(BaseModel):
    # TODO: Switch PK to GUID instead of WID (racing conditions)

    wid = IntegerField(primary_key=True)
    guid = UUIDField(index=True)
    faction_tid = IntegerField(null=False)
    amount = BigIntegerField(null=False)
    cash_request = BooleanField(default=True)

    requester = IntegerField(null=False)
    time_requested = DateTimeField(null=False)
    expires_at = DateTimeField(default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=1), null=True)

    # Withdrawal status
    # 0: unfulfilled
    # 1: fulfilled
    # 2: cancelled
    # 3: cancelled by system
    status = SmallIntegerField()

    fulfiller = IntegerField(null=True)  # -1: someone
    time_fulfilled = DateTimeField(null=True)

    withdrawal_message = BigIntegerField()  # Discord message ID
