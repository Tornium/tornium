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

import json
import random
import time
import typing
import uuid

import mongoengine
from flask import jsonify, request
from mongoengine.queryset.visitor import Q
from tornium_celery.tasks.api import tornget
from tornium_celery.tasks.reports.member_report import (
    enqueue_member_ps,
    member_ps_error,
)
from tornium_commons import rds
from tornium_commons.models import (
    FactionModel,
    MemberReportModel,
    PersonalStatModel,
    UserModel,
)

from controllers.api.decorators import (
    authentication_required,
    ratelimit,
    token_required,
)
from controllers.api.utils import api_ratelimit_response, make_exception_response


def _faction_data(tid):
    faction: typing.Optional[FactionModel] = FactionModel.objects(tid=tid).first()

    data = {
        "id": tid,
        "name": "",
    }

    if faction is not None:
        data["name"] = faction.name

    return data


@authentication_required
@ratelimit
def get_reports(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    reports: mongoengine.QuerySet
    if kwargs["user"].factionid == 0:
        reports = MemberReportModel.objects(
            Q(requested_by_user=kwargs["user"].tid) | Q(requested_by_faction=kwargs["user"].factionid)
        )
    else:
        reports = MemberReportModel.objects(requested_by_user=kwargs["user"].tid)

    return (
        jsonify(
            {
                "reports": [
                    {
                        "report_id": report.rid,
                        "created_at": report.created_at,
                        "last_updated": report.last_updated,
                        "requested_data": report.requested_data,
                        "status": report.status,
                        "faction": {**_faction_data(report.faction_id)},
                        "start_timestamp": report.start_timestamp,
                        "end_timestamp": report.end_timestamp,
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

    faction_id = data.get("faction_id")
    start_time = data.get("start_time")
    end_time = data.get("end_time", int(time.time()))
    availability = data.get("availability", "user")
    selected_stats = set(data.get("selected_stats"))

    if faction_id in ("", None, 0, "0") or not faction_id.isdigit():
        return make_exception_response("1102", key)
    elif start_time is None or type(start_time) not in (int, str):
        return make_exception_response("0000", key, details={"message": "Invalid start_time"})
    elif end_time is None or type(end_time) not in (int, str):
        return make_exception_response("0000", key, details={"message": "Invalid end_time"})
    elif availability not in ("user", "faction"):
        return make_exception_response("0000", key, details={"message": "Invalid availability"})
    elif len(selected_stats) == 0:
        return make_exception_response("0000", key, details={"message": "No personal stats selected"})

    try:
        start_time = int(start_time)
        end_time = int(end_time)
    except TypeError:
        return make_exception_response("0000", key, details={"message": "Invalid timestamp"})

    if start_time < 0 or end_time < 0 or start_time >= end_time:
        return make_exception_response("0000", key, details={"message": "Invalid start_time or end_time"})
    if end_time > int(time.time()):
        return make_exception_response("0000", key, details={"message": "Timestamps must be before right now"})
    elif availability == "faction" and not kwargs["user"].faction_aa and kwargs["user"].factionid != 0:
        return make_exception_response("4005", key)
    elif availability == "user" and kwargs["user"].key in (None, ""):
        return make_exception_response("1200", key)

    ps_keys: set = rds().smembers("tornium:personal-stats")

    if len(ps_keys) == 0:
        return make_exception_response("0000", key, details={"message": "Invalid server cache"})
    elif len(ps_keys & selected_stats) != len(selected_stats):
        return make_exception_response("0000", key, details={"message": "Invalid personal stat passed"})

    now = int(time.time())

    report = MemberReportModel(
        rid=uuid.uuid4().hex,
        created_at=now,
        last_updated=now,
        requested_data=list(selected_stats),
        start_timestamp=start_time,
        end_timestamp=end_time,
        faction_id=faction_id,
    )

    if availability == "user":
        report.requested_by_user = kwargs["user"].tid
        report.requested_by_faction = None
        keys = tuple([kwargs["user"].key])
    elif availability == "faction":
        report.requested_by_user = None
        report.requested_by_faction = kwargs["user"].factionid

        faction: typing.Optional[FactionModel] = FactionModel.objects(tid=kwargs["user"].factionid).first()

        if faction is None:
            return make_exception_response("1201", key)

        keys = tuple(faction.aa_keys)

    report.save()

    tornget.signature(
        kwargs={"endpoint": f"faction/{faction_id}?selections=basic", "key": random.choice(keys)},
        queue="api",
    ).apply_async(
        link=enqueue_member_ps.signature(
            kwargs={
                "api_keys": keys,
                "rid": report.rid,
            }
        ),
        link_error=member_ps_error.signature(kwargs={"rid": report.rid}),
    )

    return (
        {
            "report_id": report.rid,
            "created_at": report.created_at,
            "last_updated": report.last_updated,
            "requested_data": report.requested_data,
            "status": report.status,
            "faction": {**_faction_data(report.faction_id)},
            "start_timestamp": report.start_timestamp,
            "end_timestamp": report.end_timestamp,
        },
        200,
        api_ratelimit_response(key),
    )


@token_required
@ratelimit
def delete_report(rid, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    report: typing.Optional[MemberReportModel] = MemberReportModel.objects(rid=rid).first()

    if report is None:
        return make_exception_response("1000", key, details={"message": "Unknown report ID"})
    elif report.requested_by_user is not None and report.requested_by_user != kwargs["user"].tid:
        return make_exception_response("4004", key)
    elif (
        report.requested_by_faction is not None
        and report.requested_by_faction != kwargs["user"].factionid
        and not kwargs["user"].factionaa
    ):
        return make_exception_response("4005", key)

    report.delete()

    return make_exception_response("0001", key)


@token_required
@ratelimit
def get_report(rid, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    report: typing.Optional[MemberReportModel] = MemberReportModel.objects(rid=rid).first()

    if report is None:
        return make_exception_response("1000", key, details={"message": "Unknown report ID"})
    elif report.requested_by_user is not None and report.requested_by_user != kwargs["user"].tid:
        return make_exception_response("4004", key)
    elif (
        report.requested_by_faction is not None
        and report.requested_by_faction != kwargs["user"].factionid
        and not kwargs["user"].factionaa
    ):
        return make_exception_response("4005", key)

    members = {}
    start_ps = {}
    end_ps = {}

    for tid, pid in report.start_ps.items():
        if pid is None:
            start_ps[int(tid)] = None
            continue

        ps: typing.Optional[PersonalStatModel] = PersonalStatModel.objects(pstat_id=pid).first()

        if ps is None:
            start_ps[int(tid)] = None
            continue

        ps_data = {}

        for field in report.requested_data:
            ps_data[field] = ps[field]

        start_ps[int(tid)] = ps_data

    for tid, pid in report.end_ps.items():
        if pid is None:
            end_ps[int(tid)] = None
            continue

        ps: typing.Optional[PersonalStatModel] = PersonalStatModel.objects(pstat_id=pid).first()

        if ps is None:
            end_ps[int(tid)] = None
            continue

        ps_data = {}

        for field in report.requested_data:
            ps_data[field] = ps[field]

        end_ps[int(tid)] = ps_data

    for member_id in set(start_ps.keys()) | set(end_ps.keys()):
        user: typing.Optional[UserModel] = UserModel.objects(tid=member_id).first()

        if user is None:
            members[member_id] = None
            continue

        members[member_id] = {
            "name": user.name,
        }

    response = {
        "created_at": report.created_at,
        "last_updated": report.last_updated,
        "status": report.status,
        "requested_data": report.requested_data,
        "faction": {**_faction_data(report.faction_id)},
        "start_timestamp": report.start_timestamp,
        "end_timestamp": report.end_timestamp,
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
