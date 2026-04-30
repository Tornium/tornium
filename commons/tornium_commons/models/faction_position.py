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

from peewee import ArrayField, BooleanField, CharField, ForeignKeyField, UUIDField

from .base_model import BaseModel
from .faction import Faction


class FactionPosition(BaseModel):
    class Meta:
        table_name = "faction_position"

    pid = UUIDField(primary_key=True)
    name = CharField()
    faction_id = ForeignKeyField(Faction, null=False)

    default = BooleanField(default=False)
    permissions = ArrayField(CharField, default=[], null=False)
