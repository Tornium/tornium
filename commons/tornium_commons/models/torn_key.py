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

from peewee import (
    BooleanField,
    CharField,
    DeferredForeignKey,
    SmallIntegerField,
    UUIDField,
    fn,
)

from .base_model import BaseModel


class TornKey(BaseModel):
    guid = UUIDField(primary_key=True)
    api_key = CharField(max_length=16, null=False, unique=True, index=True)
    user = DeferredForeignKey("User")
    default = BooleanField(default=False)
    disabled = BooleanField(default=False)
    paused = BooleanField(default=False)  # Comes from Torn API error code 18
    access_level = SmallIntegerField(null=True)

    @classmethod
    def random_key(cls) -> typing.Optional["TornKey"]:
        return (
            TornKey.select(TornKey.api_key)
            .where((TornKey.default == True) & (TornKey.disabled == False) & (TornKey.paused == False))
            .order_by(fn.Random())
            .first()
        )
