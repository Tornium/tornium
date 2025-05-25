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
import uuid

from flask import jsonify, request
from peewee import DoesNotExist, IntegrityError
from tornium_commons.db_connection import db
from tornium_commons.models import (
    Faction,
    OrganizedCrimeNew,
    OrganizedCrimeSlot,
    OrganizedCrimeTeam,
    OrganizedCrimeTeamMember,
    User,
)

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def create_oc_team(faction_id: int, oc_name: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if oc_name not in OrganizedCrimeNew.oc_names():
        return make_exception_response("1105", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022")
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006")

    # The OC slots of the latest OC for the specified OC name need to be retrieved to determine
    # the names and indices of the positions in the OC
    try:
        latest_oc: OrganizedCrimeNew = (
            OrganizedCrimeNew.select(OrganizedCrimeNew.oc_id)
            .where(OrganizedCrimeNew.oc_name == oc_name)
            .order_by(OrganizedCrimeNew.created_at.desc())
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1105", key)

    latest_oc_slots = (
        OrganizedCrimeSlot.select()
        .where(OrganizedCrimeSlot.oc_id == latest_oc.oc_id)
        .order_by(OrganizedCrimeSlot.crime_position_index.asc())
    )
    team_members = []
    position_count = {}

    slot: OrganizedCrimeSlot
    for slot in latest_oc_slots:
        if slot.crime_position_index == -1:
            # NOTE: The index of -1 is assigned as the default and is presumed to only occur for OCs in the
            # database before the DB migration of `20250515220655_add_oc_teams.exs`
            return make_exception_response("0000", key, details={"message": "No known OC slot positioning"})

        team_members.append(
            {
                "guid": uuid.uuid4(),
                "user_id": None,
                "team_id": None,
                "faction_id": faction_id,
                "slot_type": slot.crime_position,
                "slot_count": slot.crime_position_index,
                "slot_index": position_count.get(slot.crime_position, 0),
            }
        )
        position_count[slot.crime_position] = position_count.get(slot.crime_position, 0) + 1

    guid = uuid.uuid4()
    with db().atomic():
        team: OrganizedCrimeTeam = (
            OrganizedCrimeTeam.insert(
                guid=guid,
                name=f"oc-team-{str(guid)[:8]}",
                oc_name=oc_name,
                faction=faction_id,
            )
            .returning(OrganizedCrimeTeam)
            .execute()[0]
        )

        for member in team_members:
            member["team_id"] = team.guid

        OrganizedCrimeTeamMember.insert_many(team_members).execute()

    return jsonify(team.to_dict()), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def get_oc_team(faction_id: int, team_guid: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022")
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006")

    try:
        team: OrganizedCrimeTeam = (
            OrganizedCrimeTeam.select()
            .where((OrganizedCrimeTeam.faction_id == faction_id) & (OrganizedCrimeTeam.guid == team_guid))
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1106", key)

    return jsonify(team.to_dict()), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def get_oc_teams(faction_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022")
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006")

    limit = int(request.args.get("limit", 10))
    offset = int(request.args.get("offset", 0))

    if not isinstance(limit, int) or limit <= 0:
        return make_exception_response("0000", key, details={"element": "limit"})
    elif not isinstance(offset, int) or offset < 0:
        return make_exception_response("0000", key, details={"element": "offset"})

    teams: typing.Iterable[OrganizedCrimeTeam] = (
        OrganizedCrimeTeam.select().where(OrganizedCrimeTeam.faction_id == faction_id).offset(offset).limit(limit)
    )

    return [team.to_dict() for team in teams], 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_oc_team_member(faction_id: int, team_guid: str, member_guid: str, user_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022")
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006")
    elif not OrganizedCrimeTeam.select().where(OrganizedCrimeTeam.guid == team_guid).exists():
        return make_exception_response("1106", key)
    elif not OrganizedCrimeTeamMember.select().where(OrganizedCrimeTeamMember.guid == member_guid).exists():
        return make_exception_response("1107", key)

    try:
        user: User = User.select(User.faction_id).where(User.tid == user_id).get()
    except DoesNotExist:
        return make_exception_response("1100", key)

    if user.faction_id != faction_id:
        return make_exception_response("0000", key, details={"message": "User not in faction"})

    try:
        member: OrganizedCrimeTeamMember = (
            OrganizedCrimeTeamMember.update(user=user_id)
            .where(OrganizedCrimeTeamMember.guid == member_guid)
            .returning(OrganizedCrimeTeamMember)
            .execute()[0]
        )
    except IntegrityError:
        return make_exception_response(
            "0000", key, details={"message": "User has already been set in a position on an OC team."}
        )

    return member.to_dict(), 200, api_ratelimit_response(key)
