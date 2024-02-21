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

import typing
from functools import cached_property, lru_cache

from peewee import (
    BigIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
    DeferredForeignKey,
    DoesNotExist,
    IntegerField,
)
from playhouse.postgres_ext import JSONField

from .base_model import BaseModel
from .faction_position import FactionPosition
from .torn_key import TornKey


class Faction(BaseModel):

    # Basic data
    tid = IntegerField(primary_key=True)
    name = CharField(max_length=50, null=True)
    tag = CharField(max_length=8, null=True)
    respect = IntegerField(null=True)
    capacity = IntegerField(null=True)
    leader = DeferredForeignKey("User", null=True)
    coleader = DeferredForeignKey("User", null=True)

    # Guild data
    guild = DeferredForeignKey("Server", null=True)  # noqa: F712

    # Configuration data
    stats_db_enabled = BooleanField(default=True)  # noqa: F712
    stats_db_global = BooleanField(default=True)  # noqa: F712

    # OD data
    od_channel = BigIntegerField(null=True)
    od_data = JSONField(null=True)

    # Internal data
    last_members = DateTimeField(null=True)
    last_attacks = DateTimeField(null=True)

    def get_bankers(self):
        from .user import User

        bankers = set(
            u.tid
            for u in User.select(User.tid)
            .join(FactionPosition)
            .where(
                (User.faction_id == self.tid)
                & (
                    (User.faction_position.give_money == True)
                    | (User.faction_position.give_points == True)
                    | (User.faction_position.adjust_balances == True)
                )
            )
        )

        if self.leader is not None:
            bankers.add(self.leader_id)
        if self.coleader is not None:
            bankers.add(self.coleader_id)

        return bankers

    @staticmethod
    def faction_str(tid: int) -> str:
        try:
            return f"{Faction.faction_name(tid)} [{tid}]"
        except DoesNotExist:
            return f"N/A {tid}"

    @staticmethod
    @lru_cache
    def faction_name(tid: int) -> str:
        try:
            return Faction.select(Faction.name).where(Faction.tid == tid).get().name
        except DoesNotExist:
            return "N/A"

    @cached_property
    def aa_keys(self) -> typing.List[TornKey]:
        from .user import User

        return [
            k.api_key
            for k in TornKey.select(TornKey.api_key)
            .join(User)
            .join(Faction)
            .where(
                (TornKey.user.faction.tid == self.tid)
                & (TornKey.user.faction_aa == True)
                & (TornKey.paused == False)
                & (TornKey.disabled == False)
            )
            if k.api_key != ""
        ]
