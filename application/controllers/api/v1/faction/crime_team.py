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

import uuid

from flask import jsonify
from peewee import DoesNotExist
from tornium_commons.models import Faction, OrganizedCrimeNew, OrganizedCrimeTeam

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def create_oc_team(faction_id: int, oc_name: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if oc_name not in OrganizedCrimeNew.oc_names():
        return make_exception_response("1105", key)

    try:
        faction: Faction = Faction.select().where(Faction.tid == faction_id).get()
        # TODO: Limit to required selections
    except DoesNotExist:
        return make_exception_response("1102", key)

    team_count = OrganizedCrimeTeam.select().where(OrganizedCrimeTeam.faction_id == faction_id).count()
    team: OrganizedCrimeTeam = (
        OrganizedCrimeTeam.insert(
            guid=uuid.uuid4(),
            name=f"oc-team-{team_count}",
            oc_name=oc_name,
            faction=faction.tid,
        )
        .returning(OrganizedCrimeTeam)
        .execute()[0]
    )

    return jsonify(team.to_dict()), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def get_oc_team(faction_id: int, team_guid: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    try:
        team: OrganizedCrimeTeam = (
            OrganizedCrimeTeam.select()
            .where((OrganizedCrimeTeam.faction_id == faction_id) & (OrganizedCrimeTeam.guid == team_guid))
            .get()
        )
    except DoesNotExist:
        return make_exception_response()

    return jsonify(team.to_dict()), 200, api_ratelimit_response(key)
