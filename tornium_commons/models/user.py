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

import base64
import hashlib
import os
import typing
from functools import cached_property, lru_cache

from peewee import (
    BigIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
    DoesNotExist,
    FloatField,
    ForeignKeyField,
    IntegerField,
    SmallIntegerField,
    TextField,
)
from playhouse.postgres_ext import ArrayField

from .base_model import BaseModel
from .faction import Faction
from .faction_position import FactionPosition
from .personal_stats import PersonalStats
from .torn_key import TornKey


class User(BaseModel):
    class Meta:
        table_name = "user"

    # Basic data
    tid = IntegerField(primary_key=True)
    name = CharField(max_length=15, null=True)
    level = SmallIntegerField(null=True)
    discord_id = BigIntegerField(index=True, null=True)
    personal_stats = ForeignKeyField(PersonalStats, null=True)
    # Must be the lstest personal stats entry containing all the data

    # Battle stats
    battlescore = FloatField(null=True)
    strength = BigIntegerField(null=True)
    defense = BigIntegerField(null=True)
    speed = BigIntegerField(null=True)
    dexterity = BigIntegerField(null=True)

    # Faction data
    faction = ForeignKeyField(Faction, index=True, null=True)
    faction_aa = BooleanField(default=False)
    faction_position = ForeignKeyField(FactionPosition, null=True)

    # User status
    status = TextField(null=True)
    last_action = DateTimeField(null=True)

    # Internal data
    last_refresh = DateTimeField(null=True)
    last_attacks = DateTimeField(null=True)
    battlescore_update = DateTimeField(null=True)

    # Security data
    security = SmallIntegerField(null=True)
    otp_secret = TextField(null=True)
    otp_backups = ArrayField(TextField, index=False, default=[])

    @staticmethod
    def user_str(tid: int) -> str:
        if tid == -1:
            return "Someone"

        try:
            return f"{User.user_name(tid)} [{tid}]"
        except DoesNotExist:
            return f"N/A {tid}"

    @staticmethod
    @lru_cache
    def user_name(tid: int) -> str:
        try:
            return User.select(User.name).where(User.tid == tid).get().name
        except DoesNotExist:
            return "N/A"

    def user_str_self(self) -> str:
        return f"{self.name} [{self.tid}]"

    def generate_otp_secret(self):
        self.otp_secret = base64.b32encode(os.urandom(10)).decode("utf-8")
        self.save()

    def generate_otp_url(self):
        if self.otp_secret == "" or self.security != 1:  # nosec B105
            raise Exception("Illegal OTP secret or security mode")

        return f"otpauth://totp/Tornium:{self.tid}?secret={self.otp_secret}&Issuer=Tornium"

    def generate_otp_backups(self, num_codes=5):
        if self.otp_secret == "" or self.security != 1:  # nosec B105
            raise Exception("Illegal OTP secret or security mode")

        codes = []
        hashed_codes = []

        for _ in range(num_codes):
            codes.append(base64.b32encode(os.urandom(10)).decode("utf-8"))

        for code in codes:
            hashed_codes.append(hashlib.sha256(code.encode("utf-8")).hexdigest())

        self.otp_backups = hashed_codes
        self.save()

        return codes

    @cached_property
    def key(self) -> typing.Optional[str]:
        def _v(k):
            if k == "":
                return None
            return k

        api_keys = TornKey.select(TornKey.api_key).where(
            (TornKey.user_id == self.tid) & (TornKey.paused == False) & (TornKey.disabled == False)
        )
        keys_count = api_keys.count()

        if keys_count == 0:
            return None
        elif keys_count == 1:
            try:
                return _v(api_keys.get().api_key)
            except DoesNotExist:
                return None

        try:
            return _v(api_keys.where(TornKey.default == True).get().api_key)
        except DoesNotExist:
            pass

        try:
            return _v(api_keys.where(TornKey.access_level << [3, 4]).get().api_key)
        except DoesNotExist:
            return None
