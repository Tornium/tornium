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
    BigIntegerField,
    BooleanField,
    CompositeKey,
    ForeignKeyField,
    IntegerField,
)
from playhouse.postgres_ext import ArrayField

from .base_model import BaseModel
from .faction import Faction
from .server import Server


class ServerAttackConfig(BaseModel):
    # Used for primary key
    faction = ForeignKeyField(Faction)
    server = ForeignKeyField(Server, backref="attacks_config")

    # Retaliation
    retal_channel = BigIntegerField(null=True)
    retal_roles = ArrayField(BigIntegerField, index=False, default=[])
    retal_wars = BooleanField(default=False, null=False)

    # Chain Bonus
    chain_bonus_channel = BigIntegerField(null=True)
    chain_bonus_roles = ArrayField(BigIntegerField, index=False, default=[])
    chain_bonus_length = IntegerField(null=False, default=100)

    # Chain Alert
    chain_alert_channel = BigIntegerField(null=True)
    chain_alert_roles = ArrayField(BigIntegerField, index=False, default=[])
    chain_alert_minimum = IntegerField(default=60, null=False)

    class Meta:
        primary_key = CompositeKey("faction", "server")
