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

from peewee import DateTimeField, ForeignKeyField, SmallIntegerField
from playhouse.postgres_ext import UUIDField

from tornium_commons.formatters import timestamp

from .base_model import BaseModel
from .faction import Faction


class SteadfastEvent(BaseModel):
    class Meta:
        table_name = "steadfast_event"

    guid = UUIDField(primary_key=True)
    faction = ForeignKeyField(Faction, null=False)

    strength = SmallIntegerField(null=False)
    defense = SmallIntegerField(null=False)
    speed = SmallIntegerField(null=False)
    dexterity = SmallIntegerField(null=False)

    start_timestamp = DateTimeField(null=False)
    end_timestamp = DateTimeField(null=False)

    def to_dict(self):
        return {
            "guid": self.guid,
            "category": "steadfast_event",
            "steadfast": {
                "strength": self.strength,
                "defense": self.defense,
                "speed": self.speed,
                "dexterity": self.dexterity,
            },
            "starts_at": timestamp(self.start_timestamp),
            "ends_at": timestamp(self.end_timestamp),
        }
