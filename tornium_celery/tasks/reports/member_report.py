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
import logging
import time
import typing

import celery
from celery.utils.log import get_task_logger
from tornium_commons import rds
from tornium_commons.models import (
    FactionModel,
    MemberReportModel,
    PersonalStatModel,
    UserModel,
)

from ..api import tornget

logger: logging.Logger = get_task_logger("celery_app")


@celery.shared_task(name="tasks.reports.member_ps_error", routing_key="quick.reports.member_ps_error", queue="quick")
def member_ps_error(request, exc, traceback, rid: str):
    report: typing.Optional[MemberReportModel] = MemberReportModel.objects(rid=rid).first()

    if report is not None:
        report.status = 999
        report.save()


@celery.shared_task(
    name="tasks.reports.member_ps_success", routing_key="quick.reports.member_ps_success", queue="quick"
)
def member_ps_success(rid: str):
    report: typing.Optional[MemberReportModel] = MemberReportModel.objects(rid=rid).first()

    if report is not None and report.status == 1:
        report.status = 2
        report.save()


@celery.shared_task(
    name="tasks.reports.enqueue_member_ps", routing_key="default.reports.enqueue_member_ps", queue="default"
)
def enqueue_member_ps(faction_data: dict, api_keys: tuple, rid: str):
    if len(api_keys) == 0:
        raise ValueError("No API calls provided")

    try:
        FactionModel.objects(tid=faction_data["ID"]).modify(
            upsert=True,
            new=True,
            set__name=faction_data["name"],
            set__tag=faction_data["tag"],
            set__respect=faction_data["respect"],
            set__capacity=faction_data["capacity"],
            set__leader=faction_data["leader"],
            set__coleader=faction_data["co-leader"],
        )
    except Exception as e:
        logger.exception(e)

    call_count = 0
    report: typing.Optional[MemberReportModel] = MemberReportModel.objects(rid=rid).first()

    if report is None:
        logger.debug(f"No report found - {rid}")
        raise ValueError("Illegal RID")

    requested_stats = ",".join(tuple(report.requested_data))

    for member_id, member_data in faction_data["members"].items():
        # Max 25 calls per key per minute
        try:
            UserModel.objects(tid=int(member_id)).modify(
                upsert=True,
                new=True,
                set__name=member_data["name"],
                set__level=member_data["level"],
                set__last_refresh=int(time.time()),
                set__factionid=faction_data["ID"],
                set__status=member_data["last_action"]["status"],
                set__last_action=member_data["last_action"]["timestamp"],
            )
        except Exception as e:
            logger.exception(e)
            raise e

        # If the member has joined since the report's start timestamp
        # Not always effective if the member has been in the faction before
        if member_data["days_in_faction"] < (int(time.time()) - report.start_timestamp) / (3600 * 24):
            from_ts = int(time.time()) - member_data["days_in_faction"] * 24 * 3600
        else:
            from_ts = report.start_timestamp

        logger.info(
            f"User {member_data['name']} [{member_id}] - from {from_ts} - countdown {60 * (call_count // (len(api_keys) * 25))}"
        )
        tornget.signature(
            kwargs={
                "endpoint": f"user/{member_id}?selections=personalstats&stat={requested_stats}&timestamp={from_ts}",
                "key": api_keys[call_count % len(api_keys)],
            }
        ).apply_async(
            countdown=60 * (call_count // (len(api_keys) * 25)),
            link=store_member_ps.signature(
                kwargs={
                    "tid": int(member_id),
                    "rid": rid,
                    "timestamp": from_ts,
                },
                queue="quick",
            ),
        )
        call_count += 1

    for member_id, member_data in faction_data["members"].items():
        logger.info(
            f"User {member_data['name']} [{member_id}] - to {report.end_timestamp} - countdown {60 * (call_count // (len(api_keys) * 25) + 1)}"
        )
        tornget.signature(
            kwargs={
                "endpoint": f"user/{member_id}?selections=personalstats&stat={requested_stats}&timestamp={report.end_timestamp}",
                "key": api_keys[call_count % len(api_keys)],
            }
        ).apply_async(
            countdown=60 * (call_count // (len(api_keys) * 25) + 1),
            link=store_member_ps.signature(
                kwargs={
                    "tid": int(member_id),
                    "rid": rid,
                    "timestamp": report.end_timestamp,
                },
                queue="quick",
            ),
        )
        call_count += 1

    member_ps_success.apply_async(
        countdown=60 * (call_count // (len(api_keys) * 25) + 2),
        kwargs={
            "rid": rid,
        },
    )

    rds().set(
        f"tornium:report:{rid}:endtime",
        int(time.time()) + 60 * (call_count // (len(api_keys) * 25) + 1),
        nx=True,
        ex=60 * (call_count // (len(api_keys) * 25) + 3),
    )


@celery.shared_task(name="tasks.reports.store_member_ps", routing_key="quick.reports.store_member_ps", queue="quick")
def store_member_ps(member_data: dict, tid: int, rid: str, timestamp: int):
    # timestamp must be in UTC

    try:
        if member_data.get("personalstats") is None:
            raise ValueError("Invalid API data")

        report: typing.Optional[MemberReportModel] = MemberReportModel.objects(rid=rid).first()

        if report is None:
            raise ValueError("Illegal RID")
        elif report.start_timestamp > timestamp > report.end_timestamp:
            raise ValueError("Illegal timestamp")

        timestamp = int(datetime.datetime.fromtimestamp(timestamp).replace(minute=0, second=0).timestamp())

        if report.end_timestamp == timestamp:
            logger.info(f"Storing {tid} for {timestamp} as end timestamp")
        else:
            logger.info(f"Storing {tid} for {timestamp} as start timestamp")

        pid = int(bin(tid << 8), 2) + int(bin(timestamp), 2)

        try:
            PersonalStatModel(
                **dict(
                    {
                        "pstat_id": pid,
                        "tid": tid,
                        "timestamp": timestamp,
                    },
                    **(member_data["personalstats"]),
                )
            ).save()
        except Exception as e:
            if timestamp == report.end_timestamp:
                report.end_ps[str(tid)] = None
            else:
                report.start_ps[str(tid)] = None

            raise e

        if timestamp == report.end_timestamp:
            report.end_ps[str(tid)] = pid
        else:
            report.start_ps[str(tid)] = pid

        if report.status == 0:
            report.status = 1

        now = int(time.time())

        if report.last_updated < now:
            report.last_updated = now

        report.save()
    except Exception as e:
        logger.exception(e)
        raise e
