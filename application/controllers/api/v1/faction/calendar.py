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
import json
import uuid

from flask import jsonify, request
from peewee import IntegrityError
from tornium_commons.models import Faction, SteadfastEvent, TornEvent

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth("faction:calendar", "faction")
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
    steadfast_events = SteadfastEvent.select().where(
        (SteadfastEvent.faction_id == faction_id)
        & (SteadfastEvent.start_timestamp <= to_timestamp)
        & (SteadfastEvent.end_timestamp >= from_timestamp)
    )

    events = [event.to_dict() for category_events in (steadfast_events, torn_events) for event in category_events]
    sorted_events = sorted(events, key=lambda event: event["starts_at"])

    return jsonify(sorted_events), 200, api_ratelimit_response(key)


@require_oauth("faction:calendar", "faction")
@ratelimit
def create_steadfast_event(faction_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)
    elif not kwargs["user"].faction_aa:
        return make_exception_response("4005", key)

    try:
        steadfast_data = data["steadfast"]
        from_value = int(data["from"])
        to_value = int(data["to"])
    except KeyError:
        return make_exception_response(
            "1000", key, details={"message": "The from and to timestamps and the steadfast data must be provided."}
        )
    except ValueError:
        return make_exception_response("1000", key, details={"message": "The from/to timestamps must be integers."})

    if from_value > to_value:
        return make_exception_response(
            "1000", key, details={"message": "The from timestamp must be before the to timestamp."}
        )

    from_timestamp = datetime.datetime.fromtimestamp(from_value, tz=datetime.timezone.utc)
    to_timestamp = datetime.datetime.fromtimestamp(to_value, tz=datetime.timezone.utc)

    try:
        steadfast_values = {
            "strength": int(steadfast_data["strength"]),
            "defense": int(steadfast_data["defense"]),
            "speed": int(steadfast_data["speed"]),
            "dexterity": int(steadfast_data["dexterity"]),
        }
    except KeyError:
        return make_exception_response(
            "1000",
            key,
            details={"message": "The strength, defense, sped, and dexterity steadfast data must be provided."},
        )
    except ValueError:
        return make_exception_response("1000", key, details={"message": "The steadfast values must be integers."})

    if not all(0 <= steadfast <= 20 for steadfast in steadfast_values.values()):
        return make_exception_response(
            "1000", key, details={"message": "The steadfast values must be between 0 and 20."}
        )
    elif 11 <= steadfast_values["strength"] <= 15 and 11 <= steadfast_values["defense"] <= 15:
        return make_exception_response(
            "1000", key, details={"message": "Only one of strength and defense can be between 11% and 15%."}
        )
    elif 11 <= steadfast_values["speed"] <= 15 and 11 <= steadfast_values["dexterity"] <= 15:
        return make_exception_response(
            "1000", key, details={"message": "Only one of speed and dexterity can be between 11% and 15%."}
        )
    elif sum(steadfast > 15 for steadfast in steadfast_values.values()) > 1:
        return make_exception_response(
            "1000", key, details={"message": "Only one steadfast value can be greater than 15%."}
        )

    try:
        event: SteadfastEvent = (
            SteadfastEvent.insert(
                guid=uuid.uuid4(),
                faction_id=faction_id,
                start_timestamp=from_timestamp,
                end_timestamp=to_timestamp,
                **steadfast_values,
            )
            .returning(SteadfastEvent)
            .execute()[0]
        )
    except IntegrityError:
        return make_exception_response(
            "1000", key, details={"message": "Steadfast event already exists during this period."}
        )

    return event.to_dict(), 200, api_ratelimit_response(key)
