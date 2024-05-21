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
    DateTimeField,
    ForeignKeyField,
    SmallIntegerField,
)
from playhouse.postgres_ext import JSONField

from .base_model import BaseModel
from .user import User


class Notification(BaseModel):
    ###############
    # Notification types
    #
    # 0: stocks price reach
    # 1: user stakeout
    # 2: faction stakeout
    # 3: item notif
    ###############

    invoker = ForeignKeyField(User)
    time_created = DateTimeField()

    recipient = BigIntegerField()
    recipient_guild = BigIntegerField()  # 0: DM

    n_type = SmallIntegerField()
    target = BigIntegerField()
    persistent = BooleanField()
    enabled = BooleanField(default=False)
    options = JSONField(index=False)
