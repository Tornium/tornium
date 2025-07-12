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

import typing

from peewee import CharField, ForeignKeyField, IntegerField, UUIDField

from .base_model import BaseModel
from .faction import Faction
from .organized_crime_cpr import OrganizedCrimeCPR
from .organized_crime_team import OrganizedCrimeTeam
from .user import User


class OrganizedCrimeTeamMember(BaseModel):
    class Meta:
        table_name = "organized_crime_team_member"
        # TODO: Add unique index on (user_id, faction_id)

    guid = UUIDField(primary_key=True)
    user = ForeignKeyField(User, null=True)
    team = ForeignKeyField(OrganizedCrimeTeam, null=False)
    faction = ForeignKeyField(Faction, null=False)

    slot_type = CharField(null=False)
    slot_count = IntegerField(null=False)
    slot_index = IntegerField(null=False)

    def to_dict(self) -> dict:
        if self.user is None:
            return {
                "guid": self.guid,
                "user": None,
                "team": self.team_id,
                "slot_type": self.slot_type,
                "slot_count": self.slot_count,
                "slot_index": self.slot_index,
            }
        else:
            cpr: typing.Optional[OrganizedCrimeCPR] = (
                OrganizedCrimeCPR.select(OrganizedCrimeCPR.cpr)
                .where(
                    (OrganizedCrimeCPR.user == self.user)
                    & (OrganizedCrimeCPR.oc_name == self.team.oc_name)
                    & (OrganizedCrimeCPR.oc_position == self.slot_type)
                )
                .first()
            )

            return {
                "guid": self.guid,
                "user": {
                    "tid": self.user_id,
                    "name": User.user_name(self.user_id),
                    "cpr": cpr.cpr if cpr is not None else None,
                },
                "team": self.team_id,
                "slot_type": self.slot_type,
                "slot_count": self.slot_count,
                "slot_index": self.slot_index,
            }
