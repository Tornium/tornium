# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import json
import random
import time
import typing
import uuid

from flask import jsonify, request
from peewee import DoesNotExist
from tornium_celery.tasks.api import tornget
from tornium_celery.tasks.reports.member_report import (
    enqueue_member_ps,
    member_ps_error,
)
from tornium_commons import rds
from tornium_commons.models import Faction, MemberReport, PersonalStats, User

from controllers.api.v1.bot.config import _faction_data
from controllers.api.v1.decorators import (
    authentication_required,
    ratelimit,
    token_required,
)
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@authentication_required
@ratelimit
def get_reports(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if kwargs["user"].faction is not None:
        reports: typing.Iterable[MemberReport] = MemberReport.select().where(
            (MemberReport.requested_by_user == kwargs["user"].tid)
            | (MemberReport.requested_by_faction == kwargs["user"].faction.tid)
        )
    else:
        reports: typing.Iterable[MemberReport] = MemberReport.select().where(
            MemberReport.requested_by_user == kwargs["user"].tid
        )

    return (
        jsonify(
            {
                "reports": [
                    {
                        "report_id": report.rid,
                        "created_at": report.created_at.timestamp(),
                        "last_updated": report.last_updated.timestamp(),
                        "requested_data": report.requested_data,
                        "status": report.status,
                        "faction": {**_faction_data(report.faction_tid)},
                        "start_timestamp": report.start_timestamp.timestamp(),
                        "end_timestamp": report.end_timestamp.timestamp(),
                    }
                    for report in reports
                ],
                "count": reports.count(),
            }
        ),
        200,
        api_ratelimit_response(key),
    )


@token_required
@ratelimit
def create_report(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        faction_tid = data["faction_id"]
    except (KeyError, ValueError):
        return make_exception_response("1102", key)

    try:
        start_time = int(data["start_time"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("0000", key, details={"message": "Invalid start time"})

    try:
        end_time = int(data.get("end_time", int(time.time())))
    except (ValueError, TypeError):
        return make_exception_response("0000", key, details={"message": "Invalid end time"})

    availability = data.get("availability", "user")

    try:
        selected_stats = set(data["selected_stats"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("0000", key, details={"message": "Invalid selected stats"})

    if type(faction_tid) not in (str, int):
        return make_exception_response("1102", key)
    elif availability not in ("user", "faction"):
        return make_exception_response("0000", key, details={"message": "Invalid availability"})
    elif len(selected_stats) == 0:
        return make_exception_response("0000", key, details={"message": "No personal stats selected"})

    if availability == "faction":
        return make_exception_response(
            "0000",
            key,
            details={"message": "During the test period, faction availability isn't permitted"},
        )

    if type(faction_tid) == str and not faction_tid.isdigit():
        try:
            faction: Faction = Faction.get(
                Faction.name**faction_tid
            )  # ** = ILIKE (case-insensitive pattern matching)
        except DoesNotExist:
            return make_exception_response("1102", key)

        faction_tid = faction.tid

    try:
        # round (floor) to unix timestamp of current day
        start_time = int(start_time) // 86400 * 86400
        end_time = int(end_time) // 86400 * 86400
    except TypeError:
        return make_exception_response("0000", key, details={"message": "Invalid timestamp"})

    if start_time < 0 or end_time < 0 or start_time >= end_time:
        return make_exception_response("0000", key, details={"message": "Invalid start_time or end_time"})
    elif end_time > int(time.time()):
        return make_exception_response("0000", key, details={"message": "Timestamps must be before right now"})
    elif end_time - start_time < 3600 * 24 * 2:  # Two days
        return make_exception_response(
            "0000",
            key,
            details={"message": "The duration of the report must be at least 2 days"},
        )
    elif availability == "faction" and not kwargs["user"].faction_aa and kwargs["user"].faction is not None:
        return make_exception_response("4005", key)
    elif availability == "user" and kwargs["user"].key in (None, ""):
        return make_exception_response("1200", key)

    ps_keys: set = rds().smembers("tornium:personal-stats")

    if len(ps_keys) == 0:
        return make_exception_response("0000", key, details={"message": "Invalid server cache"})
    elif len(ps_keys & selected_stats) != len(selected_stats):
        return make_exception_response("0000", key, details={"message": "Invalid personal stat passed"})

    rid = uuid.uuid4().hex

    report = MemberReport(
        rid=rid,
        created_at=datetime.datetime.utcnow(),
        last_updated=datetime.datetime.utcnow(),
        requested_data=list(selected_stats),
        start_timestamp=datetime.datetime.fromtimestamp(start_time, tz=datetime.timezone.utc),
        end_timestamp=datetime.datetime.fromtimestamp(end_time, tz=datetime.timezone.utc),
        faction_id=faction_tid,
    )

    if availability == "user":
        report.requested_by_user = kwargs["user"].tid
        report.requested_by_faction = None
        keys = tuple([kwargs["user"].key])
    elif availability == "faction":
        report.requested_by_user = None
        report.requested_by_faction = kwargs["user"].factionid

        faction: Faction = kwargs["user"].faction

        if faction is None:
            return make_exception_response("1201", key)

        keys = tuple(faction.aa_keys)
    else:
        raise Exception()

    report.save()

    tornget.signature(
        kwargs={
            "endpoint": f"faction/{faction_tid}?selections=basic",
            "key": random.choice(keys),
        },
        queue="api",
    ).apply_async(
        link=enqueue_member_ps.signature(
            kwargs={
                "api_keys": keys,
                "rid": rid,
            }
        ),
        link_error=member_ps_error.signature(kwargs={"rid": rid}),
    )

    return (
        {
            "report_id": rid,
            "created_at": report.created_at.timestamp(),
            "last_updated": report.last_updated.timestamp(),
            "requested_data": report.requested_data,
            "status": report.status,
            "faction": {**_faction_data(report.faction_tid)},
            "start_timestamp": report.start_timestamp.timestamp(),
            "end_timestamp": report.end_timestamp.timestamp(),
        },
        200,
        api_ratelimit_response(key),
    )


@token_required
@ratelimit
def delete_report(rid, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        report: MemberReport = MemberReport.get_by_id(rid)
    except DoesNotExist:
        return make_exception_response("1000", key, details={"message": "Unknown report ID"})

    if report.requested_by_user is not None and report.requested_by_user != kwargs["user"].tid:
        return make_exception_response("4004", key)
    elif (
        report.requested_by_faction is not None
        and report.requested_by_faction != kwargs["user"].faction.tid
        and not kwargs["user"].faction_aa
    ):
        return make_exception_response("4005", key)

    report.delete()

    return make_exception_response("0001", key)


@token_required
@ratelimit
def get_report(rid, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        report: MemberReport = MemberReport.get_by_id(rid)
    except DoesNotExist:
        return make_exception_response("1000", key, details={"message": "Unknown report ID"})

    if report.requested_by_user is not None and report.requested_by_user != kwargs["user"].tid:
        return make_exception_response("4004", key)
    elif (
        report.requested_by_faction is not None
        and report.requested_by_faction != kwargs["user"].faction.tid
        and not kwargs["user"].faction_aa
    ):
        return make_exception_response("4005", key)

    members = {}
    start_ps = {}
    end_ps = {}

    for pid in report.start_ps:
        if pid is None:
            continue

        try:
            ps: PersonalStats = PersonalStats.get_by_id(pid)
        except DoesNotExist:
            continue

        ps_data = {}

        for field in report.requested_data:
            ps_data[field] = ps.ps_data[field]

        start_ps[int(ps.tid)] = ps_data

    for pid in report.end_ps:
        if pid is None:
            continue

        try:
            ps: PersonalStats = PersonalStats.get_by_id(pid)
        except DoesNotExist:
            continue

        ps_data = {}

        for field in report.requested_data:
            ps_data[field] = ps.ps_data[field]

        end_ps[int(ps.tid)] = ps_data

    for member_id in set(start_ps.keys()) | set(end_ps.keys()):
        try:
            user: User = User.get_by_id(member_id)
        except DoesNotExist:
            members[member_id] = None
            continue

        members[member_id] = {
            "name": user.name,
        }

    response = {
        "created_at": report.created_at.timestamp(),
        "last_updated": report.last_updated.timestamp(),
        "status": report.status,
        "requested_data": report.requested_data,
        "faction": {**_faction_data(report.faction_tid)},
        "start_timestamp": report.start_timestamp.timestamp(),
        "end_timestamp": report.end_timestamp.timestamp(),
        "start_data": start_ps,
        "end_data": end_ps,
        "members": members,
    }

    end_time = rds().get(f"tornium:report:{rid}:endtime") if report.status < 2 else None

    if end_time is not None:
        response["expected_end_time"] = int(end_time)

    return (
        response,
        200,
        api_ratelimit_response(key),
    )
