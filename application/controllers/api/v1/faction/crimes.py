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

import datetime
import typing

from flask import request
from tornium_celery.tasks.faction import ORGANIZED_CRIMES
from tornium_commons.models import OrganizedCrime, User

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth(["faction:crimes", "faction"])
@ratelimit
def crimes_data(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    user: User = kwargs["user"]

    if user.faction is None:
        return make_exception_response("1102", key)

    limit = request.args.get("limit", 10)
    crime_types: typing.List[int] = request.args.getlist("oc-type")
    offset = request.args.get("offset", 0)
    from_ts = request.args.get("from-timestamp")
    to_ts = request.args.get("to-timestamp")
    participants = request.args.getlist("participants")

    # TODO: Input value validation

    if from_ts is not None:
        from_ts = int(from_ts)

    if to_ts is not None:
        to_ts = int(to_ts)

    crimes = (
        OrganizedCrime.select(
            OrganizedCrime.oc_id,
            OrganizedCrime.crime_id,
            OrganizedCrime.participants,
            OrganizedCrime.time_started,
            OrganizedCrime.time_ready,
            OrganizedCrime.time_completed,
            OrganizedCrime.planned_by,
            OrganizedCrime.initiated_by,
            OrganizedCrime.money_gain,
            OrganizedCrime.respect_gain,
            OrganizedCrime.delayers,
            OrganizedCrime.canceled,
        )
        .where(OrganizedCrime.faction_tid == user.faction_id)
        .limit(limit)
        .offset(offset)
    )

    if crime_types is not None and len(crime_types) > 0:
        crimes = crimes.where(OrganizedCrime.crime_id.in_(crime_types))

    if from_ts is not None:
        crimes = crimes.where(
            OrganizedCrime.time_started >= datetime.datetime.fromtimestamp(from_ts, tz=datetime.timezone.utc)
        )

    if to_ts is not None:
        crimes = crimes.where(
            OrganizedCrime.time_started <= datetime.datetime.fromtimestamp(to_ts, tz=datetime.timezone.utc)
        )

    if participants is not None and len(participants) > 0:
        crimes = crimes.where(OrganizedCrime.participants.contains_any(participants))

    return (
        {
            "crimes": [
                {
                    "id": crime.oc_id,
                    "crime_type": ORGANIZED_CRIMES[crime.crime_id],
                    "participants": [
                        {
                            "id": participant,
                            "name": User.user_name(participant),
                        }
                        for participant in crime.participants
                    ],
                    "time_started": (None if crime.time_started is None else int(crime.time_started.timestamp())),
                    "time_ready": (None if crime.time_ready is None else int(crime.time_ready.timestamp())),
                    "time_completed": (None if crime.time_completed is None else int(crime.time_completed.timestamp())),
                    "planned_by": {
                        "id": crime.planned_by_id,
                        "name": (None if crime.planned_by is None else crime.planned_by.name),
                    },
                    "initiated_by": {
                        "id": crime.initiated_by_id,
                        "name": (None if crime.initiated_by is None else crime.initiated_by.name),
                    },
                    "money_gain": crime.money_gain,
                    "respect_gain": crime.respect_gain,
                    "delayers": [delayer for delayer in crime.delayers],
                    "canceled": crime.canceled,
                }
                for crime in crimes
            ]
        },
        200,
        api_ratelimit_response(key),
    )
