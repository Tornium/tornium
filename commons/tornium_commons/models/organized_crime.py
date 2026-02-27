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

from __future__ import annotations

import typing
from functools import lru_cache

from peewee import (
    BigIntegerField,
    CharField,
    DateTimeField,
    DeferredForeignKey,
    ForeignKeyField,
    SmallIntegerField,
)
from tornium_oc_graph import calculate_ev, calculate_probability

from .base_model import BaseModel
from .faction import Faction

if typing.TYPE_CHECKING:
    from .organized_crime_slot import OrganizedCrimeSlot


class OrganizedCrime(BaseModel):
    class Meta:
        table_name = "organized_crime"

    oc_id = BigIntegerField(primary_key=True)
    oc_name = CharField(null=False)
    oc_difficulty = SmallIntegerField(null=False)

    faction = ForeignKeyField(Faction, null=False)

    status = CharField(null=False)

    created_at = DateTimeField(null=False)
    planning_started_at = DateTimeField(default=None, null=True)
    ready_at = DateTimeField(default=None, null=True)
    expires_at = DateTimeField(default=None, null=True)
    executed_at = DateTimeField(default=None, null=True)

    # Tornium-specific OC data
    assigned_team = DeferredForeignKey("OrganizedCrimeTeam", default=None, null=True)

    @classmethod
    @lru_cache
    def oc_names(cls) -> typing.List[str]:
        return [crime.oc_name for crime in OrganizedCrime.select().distinct(OrganizedCrime.oc_name)]

    def to_dict(self) -> dict:
        # Skip the `assigned_team` to avoid circular imports
        # At this time, there isn't a purpose in returning that, but if necessary in the future, this can
        # be done with an optional parameter.

        return {
            "oc_id": self.oc_id,
            "oc_name": self.oc_name,
            "oc_difficulty": self.oc_difficulty,
            "faction_id": self.faction_id,
            "status": self.status,
            "created_at": self.created_at.timestamp(),
            "planning_started_at": None if self.planning_started_at is None else self.planning_started_at.timestamp(),
            "ready_at": None if self.ready_at is None else self.ready_at.timestamp(),
            "expires_at": self.expires_at.timestamp(),
            "executed_at": None if self.executed_at is None else self.executed_at.timestamp(),
        }

    @staticmethod
    def expected_value(oc_name: str, slots: typing.List[OrganizedCrimeSlot], default=None) -> float:
        succcess_map = {}

        slot: OrganizedCrimeSlot
        for slot in slots:
            if slot.user_id is None and default is None:
                raise ValueError(f"{slot.crime_position} #{slot.crime_position_index} is not filled")

            position = f"{'_'.join(slot.crime_position.lower().split(' '))}_{slot.crime_position_index}"
            succcess_map[position] = default if slot.user_id is None else slot.user_success_chance / 100

        return calculate_ev(oc_name, succcess_map)

    @staticmethod
    def probability(oc_name: str, slots: typing.List[OrganizedCrimeSlot], default=None) -> float:
        succcess_map = {}

        slot: OrganizedCrimeSlot
        for slot in slots:
            if slot.user_id is None and default is None:
                raise ValueError(f"{slot.crime_position} #{slot.crime_position_index} is not filled")

            position = f"{"_".join(slot.crime_position.lower().split(" "))}_{slot.crime_position_index}"
            succcess_map[position] = default if slot.user_id is None else slot.user_success_chance / 100

        return calculate_probability(oc_name, succcess_map)
