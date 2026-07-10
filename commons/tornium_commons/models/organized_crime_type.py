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

from peewee import CharField, DeferredForeignKey, SmallIntegerField, TextField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel


class OrganizedCrimeType(BaseModel):
    class Meta:
        table_name = "organized_crime_type"

    guid = UUIDField(primary_key=True)

    name = CharField(null=False)
    description = TextField(null=False)

    difficulty = SmallIntegerField(null=False)
    spawn_level = SmallIntegerField(null=False)
    # spawn level values: [lambda: 1, sigma: 2, phi: 3, psi: 4, omega: 5])

    prerequisite = DeferredForeignKey("OrganizedCrimeSlotType", default=None, null=True)
