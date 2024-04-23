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

from flask import jsonify, request
from peewee import DoesNotExist
from tornium_celery.tasks.user import update_user
from tornium_commons.models import Stat, User

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth()
@ratelimit
def generate_chain_list(*args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    sort = request.args.get("sort", "timestamp")

    try:
        difficulty = int(request.args.get("difficulty", 2))
        limit = int(request.args.get("limit", 10))
    except (KeyError, ValueError, TypeError):
        return make_exception_response(
            "1000",
            key,
            details={"message": "Illegal parameter type. Must be a float or integer."},
        )

    if not (0 <= difficulty <= 4):
        return make_exception_response(
            "1000",
            key,
            details={"message": "An invalid difficulty has been provided."},
        )
    elif not (10 <= limit <= 100):
        return make_exception_response(
            "1000",
            key,
            details={"message": "An invalid limit has been provided."},
        )
    elif sort not in ("timestamp", "respect", "random"):
        return make_exception_response(
            "1000",
            key,
            details={"message": "An invalid sort option has been provided."},
        )
    elif kwargs["user"].battlescore == 0:
        return make_exception_response(
            "0000",
            key,
            details={"message": "User does not have a stat score stored in the database."},
        )

    try:
        jsonified_stat_entries = Stat.generate_chain_list(
            sort=sort, limit=limit, difficulty=difficulty, invoker=kwargs["user"]
        )
    except ValueError:
        return make_exception_response(
            "1000",
            key,
            details={"message": "An invalid parameter has been provided."},
        )

    return (
        jsonify(
            {
                "data": jsonified_stat_entries,
            }
        ),
        200,
        api_ratelimit_response(key),
    )


@require_oauth()
@ratelimit
def get_stat_user(tid: int, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    stat_entries = (
        Stat.select()
        .where(((Stat.added_group == 0) | (Stat.added_group == kwargs["user"].faction_id)) & (Stat.tid == tid))
        .order_by(-Stat.time_added)
        .limit(10)
    )

    data: dict = {"user": {}, "stat_entries": {}}

    update_user(kwargs["user"].key, tid=tid)

    try:
        user: User = User.get_by_id(tid)
    except DoesNotExist:
        return make_exception_response("1100", key)

    data["user"] = {
        "tid": user.tid,
        "name": user.name,
        "level": user.level,
        "last_refresh": user.last_refresh,
        "discord_id": user.discord_id,
        "faction": (
            {"tid": user.faction.tid, "name": user.faction.name}
            if user.faction is not None
            else {"tid": 0, "name": "None"}
        ),
        "status": user.status,
        "last_action": user.last_action,
    }

    stat_entry: Stat
    for stat_entry in stat_entries:
        data["stat_entries"][str(stat_entry.get_id())] = {
            "stat_score": stat_entry.battlescore,
            "timeadded": stat_entry.time_added.timestamp(),
        }

    return jsonify(data), 200, api_ratelimit_response(key)
