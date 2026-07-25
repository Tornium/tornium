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

import csv
import datetime
import io

from flask import make_response, request
from peewee import fn
from tornium_commons.formatters import timestamp
from tornium_commons.models import OverdoseEvent, User

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import (
    api_ratelimit_response,
    get_list,
    make_exception_response,
)


@require_oauth("faction")
@ratelimit
def get_events(faction_id: int, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]

    if user.faction_id != faction_id:
        return make_exception_response("4022", key)

    now = int(datetime.datetime.utcnow().timestamp())

    try:
        limit = int(request.args.get("limit", 25))
        offset = int(request.args.get("offset", 0))
        from_timestamp = int(request.args.get("from", 0))
        to_timestamp = int(request.args.get("to", now))
        sort_order = request.args.get("sort", "timestamp-desc")
    except (TypeError, ValueError):
        return make_exception_response("1000", key)

    members = get_list(request.args, "members", int)
    items = get_list(request.args, "items", int)

    if limit < 0 or limit > 100:
        return make_exception_response(
            "0000", key, details={"element": "limit", "message": "The limit must be between 0 and 100."}
        )
    elif offset < 0:
        return make_exception_response(
            "0000", key, details={"element": "offset", "message": "The offset must be greater than or equal to 0."}
        )
    elif from_timestamp < 0 or from_timestamp > now:
        return make_exception_response(
            "0000", key, details={"element": "from", "message": "There was an invalid from timestamp provided."}
        )
    elif to_timestamp <= 0 or to_timestamp > now:
        return make_exception_response(
            "0000", key, details={"element": "to", "message": "There was an invalid to timestamp provided."}
        )
    elif from_timestamp > to_timestamp:
        return make_exception_response(
            "0000",
            key,
            details={"element": "from+to", "message": "The from timestamp can not be larger than the to timstamp."},
        )
    # TODO: Validate item IDs

    events = OverdoseEvent.select().where(OverdoseEvent.faction_id == faction_id)

    if len(members) != 0:
        events = events.where(OverdoseEvent.user_id.in_(members))
    if from_timestamp != 0:
        events = events.where(
            OverdoseEvent.created_at >= datetime.datetime.fromtimestamp(from_timestamp, tz=datetime.timezone.utc)
        )
    if to_timestamp != now:
        events = events.where(
            OverdoseEvent.created_at <= datetime.datetime.fromtimestamp(to_timestamp, tz=datetime.timezone.utc)
        )
    if len(items) != 0:
        events = events.where(OverdoseEvent.drug_id.in_(items))

    if sort_order == "timestamp-desc":
        events = events.order_by(OverdoseEvent.created_at.desc())
    elif sort_order == "timestamp-asc":
        events = events.order_by(OverdoseEvent.created_at.asc())
    else:
        return make_exception_response(
            "0000",
            key,
            details={
                "element": "sort",
                "message": 'The sort order must be one of the following: "timestamp-desc" or "timestamp-asc".',
            },
        )

    if request.accept_mimetypes.accept_json:
        total_count_expression = fn.COUNT(OverdoseEvent.guid).over()
        events = events.select(OverdoseEvent, total_count_expression.alias("total_count"))
        paged_events = list(events.limit(limit).offset(offset))
        total_count = paged_events[0].total_count if paged_events else 0

        return (
            {"count": total_count, "overdoses": [event.to_dict() for event in paged_events]},
            200,
            api_ratelimit_response(key),
        )
    elif "text/csv" in request.accept_mimetypes:
        events = events.select(OverdoseEvent)

        buffer = io.StringIO()
        writer = csv.writer(buffer)

        header = ["timestamp", "user", "user_name", "drug"]
        data = [[timestamp(event.created_at), event.user_id, event.user.name, event.drug_id] for event in events]

        writer.writerow(header)
        writer.writerows(data)

        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = "text/csv"
        return response
    else:
        return make_exception_response("4012", key)
