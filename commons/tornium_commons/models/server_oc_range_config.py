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

from peewee import ForeignKeyField, SmallIntegerField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel
from .organized_crime_slot_type import OrganizedCrimeSlotType
from .organized_crime_type import OrganizedCrimeType
from .server_oc_config import ServerOCConfig


class ServerOCRangeConfig(BaseModel):
    class Meta:
        table_name = "server_oc_range_config"

    guid = UUIDField(null=False, primary_key=True)
    server_oc_config = ForeignKeyField(ServerOCConfig, null=False)

    oc_type = ForeignKeyField(OrganizedCrimeType, null=False)
    oc_slot_type = ForeignKeyField(OrganizedCrimeSlotType, null=False)

    minimum = SmallIntegerField(default=None, null=True)
    maximum = SmallIntegerField(default=None, null=True)

    def to_dict(self):
        return {
            "guid": self.guid,
            "server_oc_config_id": self.server_oc_config_id,
            "oc_name": self.oc_type.name,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }
