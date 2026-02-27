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

from flask import jsonify, request
from peewee import DoesNotExist, fn
from tornium_commons.models import (
    Faction,
    OrganizedCrime,
    OrganizedCrimeCPR,
    OrganizedCrimeSlot,
    User,
)

from controllers.api.v1.decorators import (
    global_cache,
    ratelimit,
    require_oauth,
    session_required,
)
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth()
@ratelimit
@global_cache
def get_oc_names(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    oc_names: typing.List[str] = [
        crime.oc_name for crime in OrganizedCrime.select().distinct(fn.LOWER(OrganizedCrime.oc_name))
    ]

    return jsonify(oc_names), 200, api_ratelimit_response(key)


@require_oauth("faction:crimes", "faction")
@ratelimit
def get_delays(faction_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    before = request.args.get("before")
    after = request.args.get("after")

    if isinstance(before, str) and not before.isdigit():
        return make_exception_response("0000", key)
    elif isinstance(after, str) and not after.isdigit():
        return make_exception_response("0000", key)

    try:
        if before is not None:
            before = int(before)
        if after is not None:
            after = int(after)

        limit = min(int(request.args.get("limit", 100)), 100)
    except (ValueError, TypeError):
        return make_exception_response("0000", key)

    if before is not None and after is not None and before >= after:
        return make_exception_response("0000", key)

    slots = (
        OrganizedCrimeSlot.select()
        .join(User)
        .where((OrganizedCrimeSlot.delayer == True) & (User.faction_id == faction_id))
        .order_by(OrganizedCrimeSlot.oc_id.desc())
        .limit(limit)
    )

    if before is not None:
        slots = slots.where(OrganizedCrimeSlot.oc_id <= before)
    if after is not None:
        slots = slots.where(OrganizedCrimeSlot.oc_id >= after)

    return [
        {
            "oc_id": slot.oc_id,
            "user_id": slot.user_id,
            "oc_position": slot.crime_position,
            "oc_position_index": slot.crime_position_index,
            "delay_reason": slot.delayed_reason,
        }
        for slot in slots
    ]


@session_required
@ratelimit
def get_members_cpr_slot(faction_id: int, oc_name: str, oc_position_name: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if oc_name not in OrganizedCrime.oc_names():
        return make_exception_response("1105", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    members = [member.tid for member in User.select(User.tid).where(User.faction_id == faction_id)]
    members_cpr: typing.Iterable[OrganizedCrimeCPR] = (
        OrganizedCrimeCPR.select()
        .join(User)
        .where(
            (User.tid.in_(members))
            & (OrganizedCrimeCPR.oc_name == oc_name)
            & (OrganizedCrimeCPR.oc_position == oc_position_name)
        )
    )

    return (
        {
            member.user_id: {
                "cpr": member.cpr,
                "name": member.user.name,
                "updated_at": int(member.updated_at.timestamp()),
            }
            for member in members_cpr
        },
        200,
        api_ratelimit_response(key),
    )


@session_required
@ratelimit
def get_members_cpr_oc(faction_id: int, oc_name: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if oc_name not in OrganizedCrime.oc_names():
        return make_exception_response("1105", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    members = [member.tid for member in User.select(User.tid).where(User.faction_id == faction_id)]
    members_cpr: typing.Iterable[OrganizedCrimeCPR] = (
        OrganizedCrimeCPR.select().join(User).where((User.tid.in_(members)) & (OrganizedCrimeCPR.oc_name == oc_name))
    )

    positions = set(member_cpr.oc_position for member_cpr in members_cpr)
    members_cpr_positions = {position: [] for position in positions}

    member_cpr: OrganizedCrimeCPR
    for member_cpr in members_cpr:
        members_cpr_positions[member_cpr.oc_position].append(member_cpr)

    for position, members_cpr_list in members_cpr_positions.items():
        members_cpr_list.sort(key=lambda member: member.cpr)

    return (
        {
            position: [
                {
                    "cpr": member.cpr,
                    "id": member.user_id,
                    "name": member.user.name,
                    "updated_at": int(member.updated_at.timestamp()),
                }
                for member in members_cpr_list
            ]
            for position, members_cpr_list in members_cpr_positions.items()
        },
        200,
        api_ratelimit_response(key),
    )


@require_oauth("faction:crimes", "faction")
@ratelimit
def get_optimum_slots(faction_id: int, user_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        user = User.select().where(User.tid == user_id).get()
    except DoesNotExist:
        return make_exception_response("1100", key)

    try:
        default_cpr = round(int(request.args.get("default_cpr", 75)) / 100, 3)
    except (TypeError, ValueError):
        return make_exception_response("0000", key, details={"message": "Invalid default CPR"})

    if default_cpr > 1 or default_cpr < 0:
        return make_exception_response("0000", key, details={"message": "The default CPR must be between 0 and 100"})
    elif user.faction_id != faction_id:
        return make_exception_response("4022", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    current_slot: typing.Optional[OrganizedCrimeSlot] = (
        OrganizedCrimeSlot.select(OrganizedCrime.oc_id, OrganizedCrime.oc_name)
        .join(OrganizedCrime)
        .where((OrganizedCrimeSlot.user_id == user_id) & (OrganizedCrime.executed_at.is_null(True)))
        .order_by(OrganizedCrimeSlot.user_joined_at.desc())
        .first()
    )
    current_ev = None

    if current_slot is not None:
        current_oc_slots: typing.List[OrganizedCrimeSlot] = list(
            OrganizedCrimeSlot.select().where(OrganizedCrimeSlot.oc_id == current_slot.oc_id)
        )

        try:
            current_ev = OrganizedCrime.expected_value(current_slot.oc.oc_name, current_oc_slots, default=1.0)
        except KeyError as e:
            return make_exception_response("0000", key, details={"message": str(e)})

    all_slots: typing.List[OrganizedCrimeSlot] = list(
        OrganizedCrimeSlot.select(
            OrganizedCrimeSlot.oc_id,
            OrganizedCrimeSlot.crime_position,
            OrganizedCrimeSlot.crime_position_index,
            OrganizedCrimeSlot.user_success_chance,
            OrganizedCrime.oc_name,
        )
        .join(OrganizedCrime)
        .where(
            (OrganizedCrime.faction_id == faction_id)
            & (OrganizedCrime.executed_at.is_null(True))
            & (OrganizedCrime.status.in_(["planning", "recruiting"]))
        )
    )

    oc_slots = {}

    slot: OrganizedCrimeSlot
    for slot in all_slots:
        oc_slots.setdefault(slot.oc_id, []).append(slot)

    user_cprs = {
        (cpr.oc_name, cpr.oc_position): cpr.cpr
        for cpr in OrganizedCrimeCPR.select(
            OrganizedCrimeCPR.oc_name, OrganizedCrimeCPR.oc_position, OrganizedCrimeCPR.cpr
        ).where(OrganizedCrimeCPR.user_id == user_id)
    }
    possible_slots = []

    for oc_id, slots in oc_slots.items():
        oc_name = slots[0].oc.oc_name
        try:
            current_oc_ev = round(OrganizedCrime.expected_value(oc_name, slots, default=0.7))
            current_oc_probability = round(OrganizedCrime.probability(oc_name, slots, default=0.7), 3)
        except KeyError:
            continue

        slot: OrganizedCrimeSlot
        for slot in slots:
            try:
                slot_cpr = user_cprs[(oc_name, slot.crime_position)]
            except Exception:
                possible_slots.append(
                    {
                        "oc_id": slot.oc_id,
                        "oc_position": slot.crime_position,
                        "oc_position_index": slot.crime_position_index,
                        "crime_success_probability": None,
                        "expected_value": None,
                        "probability": None,
                        "team_expected_value_change": None,
                        "team_probability_change": None,
                        "user_expected_value_change": None,
                    }
                )
                continue

            modified_slots = [
                (
                    set_slot
                    if set_slot != slot
                    else OrganizedCrimeSlot(
                        crime_position=set_slot.crime_position,
                        crime_position_index=set_slot.crime_position_index,
                        user_success_chance=slot_cpr,
                    )
                )
                for set_slot in slots
            ]

            try:
                expected_value = round(OrganizedCrime.expected_value(oc_name, modified_slots, default=0.7))
                probability = round(OrganizedCrime.probability(oc_name, modified_slots, default=0.7), 3)
            except KeyError:
                continue

            possible_slots.append(
                {
                    "oc_id": slot.oc_id,
                    "oc_position": slot.crime_position,
                    "oc_position_index": slot.crime_position_index,
                    "crime_success_probability": slot_cpr,
                    "expected_value": expected_value,
                    "probability": probability,
                    "team_expected_value_change": (
                        None if current_oc_ev == 0 else round((expected_value - current_oc_ev) / current_oc_ev, 4)
                    ),
                    "team_probability_change": (
                        None
                        if current_oc_probability == 0
                        else round((probability - current_oc_probability) / current_oc_probability, 4)
                    ),
                    "user_expected_value_change": (
                        None if current_ev == 0 else round((expected_value - current_ev) / current_ev, 4)
                    ),
                }
            )

    return possible_slots, 200, api_ratelimit_response(key)
