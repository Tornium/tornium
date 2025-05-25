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

from peewee import CharField, DoesNotExist, ForeignKeyField, UUIDField

from .base_model import BaseModel
from .faction import Faction
from .organized_crime_new import OrganizedCrimeNew


class OrganizedCrimeTeam(BaseModel):
    class Meta:
        table_name = "organized_crime_team"

    guid = UUIDField(primary_key=True)
    name = CharField(null=False)
    oc_name = CharField(null=False)
    faction = ForeignKeyField(Faction, null=False)

    def to_dict(self) -> dict:
        return {
            "guid": self.guid,
            "name": self.name,
            "oc_name": self.oc_name,
            "faction": self.faction_id,
            "members": self.team_members(),
            "current_crime": self.current_team_crime(),
        }

    def team_members(self):
        from .organized_crime_team_member import OrganizedCrimeTeamMember

        return [
            member.to_dict()
            for member in OrganizedCrimeTeamMember.select()
            .where(OrganizedCrimeTeamMember.team == self.guid)
            .order_by(OrganizedCrimeTeamMember.slot_count)
        ]

    def team_crimes(self):
        from .organized_crime_team_member import OrganizedCrimeTeamMember

        return [
            crime.to_dict()
            for crime in OrganizedCrimeNew.select()
            .where(OrganizedCrimeNew.assigned_team == self.guid)
            .order_by(-OrganizedCrimeNew.created_at)
        ]

    def current_team_crime(self):
        from .organized_crime_team_member import OrganizedCrimeTeamMember

        try:
            crime: OrganizedCrimeNew = (
                OrganizedCrimeNew.select()
                .where(OrganizedCrimeNew.assigned_team == self.guid)
                .order_by(-OrganizedCrimeNew.created_at)
                .get()
            )
        except DoesNotExist:
            return None

        if crime.executed_at is not None:
            return None

        return crime.to_dict()
