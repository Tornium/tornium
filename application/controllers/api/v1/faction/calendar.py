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

from flask import jsonify, request
from tornium_commons.models import Faction, TornEvent

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth("faction")
@ratelimit
def get_calendar_events(faction_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    try:
        from_value = int(request.args["from"])
        to_value = int(request.args["to"])
    except (KeyError, ValueError):
        return make_exception_response("1000", key, details={"message": "The from/to timestamps must be integers."})

    if from_value > to_value:
        return make_exception_response(
            "1000", key, details={"message": "The from timestamp must be before the to timestamp."}
        )

    from_timestamp = datetime.datetime.fromtimestamp(from_value, tz=datetime.timezone.utc)
    to_timestamp = datetime.datetime.fromtimestamp(to_value, tz=datetime.timezone.utc)

    torn_events = TornEvent.select().where(
        (TornEvent.start_timestamp <= to_timestamp) & (TornEvent.end_timestamp >= from_timestamp)
    )

    events = [event.to_dict() for category_events in (torn_events,) for event in category_events]
    sorted_events = sorted(events, key=lambda event: event["starts_at"])
    return jsonify(sorted_events), 200, api_ratelimit_response(key)
