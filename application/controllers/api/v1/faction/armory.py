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

from flask import request
from peewee import fn
from tornium_commons.models import ArmoryAction, ArmoryUsage, Item, User

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import (
    api_ratelimit_response,
    get_list,
    make_exception_response,
)

armory_action_values = [action.value for action in ArmoryAction]


@require_oauth("faction:armory", "faction")
@ratelimit
def get_logs(faction_id: int, *args, **kwargs):
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
    actions = get_list(request.args, "actions", str)
    items = get_list(request.args, "items", int)

    if limit < 0 or limit > 100:
        return make_exception_response(
            "0000", key, details={"element": "limit", "message": "The limit must be between 0 and 100."}
        )
    elif offset < 0:
        return make_exception_response(
            "0000", key, detils={"element": "offset", "message": "The offset must be greater than or equal to 0."}
        )
    elif len(actions) > 0 and any([action not in armory_action_values for action in actions]):
        return make_exception_response(
            "0000", key, details={"element": "actions", "message": "There was an invalid action provided."}
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

    logs = ArmoryUsage.select().where(ArmoryUsage.faction_id == faction_id)

    if len(members) != 0:
        logs = logs.where(ArmoryUsage.user_id.in_(members))
    if len(actions) != 0:
        logs = logs.where(ArmoryUsage.action.in_(actions))
    if from_timestamp != 0:
        logs = logs.where(
            ArmoryUsage.timestamp >= datetime.datetime.fromtimestamp(from_timestamp, tz=datetime.timezone.utc)
        )
    if to_timestamp != now:
        logs = logs.where(
            ArmoryUsage.timestamp <= datetime.datetime.fromtimestamp(to_timestamp, tz=datetime.timezone.utc)
        )
    if len(items) != 0:
        logs = logs.where(ArmoryUsage.item_id.in_(items))

    if sort_order == "timestamp-desc":
        logs = logs.order_by(ArmoryUsage.timestamp.desc())
    elif sort_order == "timestamp-asc":
        logs = logs.order_by(ArmoryUsage.timestamp.asc())
    else:
        return make_exception_response(
            "0000",
            key,
            details={
                "element": "sort",
                "message": 'The sort order must be one of the following: "timestamp-desc" or "timestamp-asc".',
            },
        )

    total_count_expression = fn.COUNT(ArmoryUsage.id).over()
    logs = logs.select(ArmoryUsage, total_count_expression.alias("total_count"))
    paged_logs = list(logs.limit(limit).offset(offset))
    total_count = paged_logs[0].total_count if paged_logs else 0

    return (
        {"count": total_count, "logs": [log.to_dict() for log in paged_logs]},
        200,
        api_ratelimit_response(key),
    )


@require_oauth("faction:armory", "faction")
@ratelimit
def get_cumulative(faction_id: int, *args, **kwargs):
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
    actions = get_list(request.args, "actions", str)
    items = get_list(request.args, "items", int)

    if limit < 0 or limit > 100:
        return make_exception_response(
            "0000", key, details={"element": "limit", "message": "The limit must be between 0 and 100."}
        )
    elif offset < 0:
        return make_exception_response(
            "0000", key, detils={"element": "offset", "message": "The offset must be greater than or equal to 0."}
        )
    elif len(actions) > 0 and any([action not in armory_action_values for action in actions]):
        return make_exception_response(
            "0000", key, details={"element": "actions", "message": "There was an invalid action provided."}
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

    total_count_expression = fn.COUNT("cumulative_usage").over().alias("total_count")
    cumulative = (
        ArmoryUsage.select(
            ArmoryUsage.action,
            ArmoryUsage.user_id,
            ArmoryUsage.item_id,
            ArmoryUsage.is_energy_refill,
            ArmoryUsage.is_nerve_refill,
            fn.SUM(ArmoryUsage.quantity).alias("cumulative_usage"),
            total_count_expression,
        )
        .where(ArmoryUsage.faction_id == faction_id)
        .group_by(
            ArmoryUsage.action,
            ArmoryUsage.user_id,
            ArmoryUsage.item_id,
            ArmoryUsage.is_energy_refill,
            ArmoryUsage.is_nerve_refill,
        )
    )

    if len(members) != 0:
        cumulative = cumulative.where(ArmoryUsage.user_id.in_(members))
    if len(actions) != 0:
        cumulative = cumulative.where(ArmoryUsage.action.in_(actions))
    if from_timestamp != 0:
        cumulative = cumulative.where(
            ArmoryUsage.timestamp >= datetime.datetime.fromtimestamp(from_timestamp, tz=datetime.timezone.utc)
        )
    if to_timestamp != now:
        cumulative = cumulative.where(
            ArmoryUsage.timestamp <= datetime.datetime.fromtimestamp(to_timestamp, tz=datetime.timezone.utc)
        )
    if len(items) != 0:
        cumulative = cumulative.where(ArmoryUsage.item_id.in_(items))

    if sort_order == "cumulative-desc":
        cumulative = cumulative.order_by(fn.SUM(ArmoryUsage.quantity).desc())
    elif sort_order == "cumulative-asc":
        cumulative = cumulative.order_by(fn.SUM(ArmoryUsage.quantity).asc())
    else:
        return make_exception_response(
            "0000",
            key,
            details={
                "element": "sort",
                "message": 'The sort order must be one of the following: "timestamp-desc" or "timestamp-asc".',
            },
        )

    paged_cumulative = list(cumulative.limit(limit).offset(offset))
    total_count = paged_cumulative[0].total_count if paged_cumulative else 0

    return (
        {
            "count": total_count,
            "cumulative": [
                {
                    "action": group.action,
                    "user": {
                        "id": group.user_id,
                        "name": User.user_name(group.user_id),
                    },
                    "item": {
                        "id": group.item_id,
                        "name": None if group.item_id is None else Item.item_name(group.item_id),
                        "is_nerve_refill": group.is_nerve_refill,
                        "is_energy_refill": group.is_energy_refill,
                    },
                    "cumulative_quantity": group.cumulative_usage,
                }
                for group in paged_cumulative
            ],
        },
        200,
        api_ratelimit_response(key),
    )
