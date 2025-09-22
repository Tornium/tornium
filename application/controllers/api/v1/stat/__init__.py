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

from flask import jsonify, request
from peewee import JOIN, SQL, DoesNotExist, fn
from tornium_celery.tasks.user import update_user
from tornium_commons import db
from tornium_commons.models import Faction, Stat, User

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

    if not (0 <= difficulty <= 5):
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
def generate_chain_list_v2(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]

    if user.battlescore in (0, None):
        return make_exception_response(
            "0000",
            key,
            details={"message": "User does not have a stat score stored in the database."},
        )

    minimum_difficulty = data.get("minimum_difficulty", 1)
    maximum_difficulty = data.get("maximum_difficulty", 3)
    minimum_level = data.get("minimum_level", 1)
    maximum_level = data.get("maximum_level", 100)
    sort_order = data.get("sort_order", "random")
    limit = data.get("limit", 25)
    is_factionless = data.get("factionless", False)
    is_inactive = data.get("inactive", False)

    try:
        minimum_difficulty = round(float(minimum_difficulty), 2)
        maximum_difficulty = round(float(maximum_difficulty), 2)
        minimum_level = int(minimum_level)
        maximum_level = int(maximum_level)
        limit = int(limit)
        is_factionless = bool(is_factionless)
        is_inactive = bool(is_inactive)
    except (TypeError, ValueError):
        return make_exception_response("0000", key, details={"message": "Invalid configuration parameter value"})

    if minimum_difficulty < 1:
        return make_exception_response(
            "0000",
            key,
            details={"message": "The minimum difficulty must be at least 1"},
        )
    elif maximum_difficulty < 1:
        return make_exception_response(
            "0000",
            key,
            details={"message": "The maximum difficulty must be at least 1"},
        )
    elif maximum_difficulty <= minimum_difficulty:
        return make_exception_response(
            "0000",
            key,
            details={"message": "The maximum difficulty must be greater than the minimum difficulty"},
        )

    if minimum_level < 1 or minimum_level > 100:
        return make_exception_response(
            "0000",
            key,
            details={"message": "The minimum level must be between 1 and 100"},
        )
    elif maximum_level < 1 or maximum_level > 100:
        return make_exception_response(
            "0000",
            key,
            details={"message": "The maximum level must be between 1 and 100"},
        )
    elif maximum_level < minimum_level:
        return make_exception_response(
            "0000",
            key,
            details={"message": "The maximum level must be greater than or equal to the minimum level"},
        )

    if sort_order not in ("recently-updated", "highest-respect", "random"):
        return make_exception_response("0000", key, details={"message": "Invalid sort order"})

    if limit < 1 or limit >= 250:
        return make_exception_response("0000", key, details={"message": "The limit must be between 1 and 250"})

    # f = fair fight
    # d = defender's stat score
    # a = attacker's stat score
    #
    # f = 1 + 8/3 * d/a
    # 0.375 * a * (f - 1) = d
    minimum_stat_score = int(0.375 * user.battlescore * (minimum_difficulty - 1))
    maximum_stat_score = int(0.375 * user.battlescore * (maximum_difficulty - 1))
    groups = (0,) if user.faction_id in (0, None) else (0, user.faction_id)

    stat_subquery = (
        Stat.select(Stat.tid_id, Stat.time_added, Stat.battlescore)
        .where(
            (Stat.time_added > SQL("NOW() - INTERVAL '6 months'"))
            & (Stat.added_group.in_(groups))
            & (Stat.battlescore.between(minimum_stat_score, maximum_stat_score))
        )
        .order_by(Stat.tid_id, Stat.time_added.desc())
        .distinct(Stat.tid_id)
    )
    s = stat_subquery.alias("s")

    fair_fight_expression = 1 + 8 / 3 * s.c.battlescore / int(user.battlescore)
    fair_fight_alias = fair_fight_expression.alias("fair_fight")
    respect_expression = (fn.ROUND((User.level / SQL("198.0")) + SQL("197.0 / 198.0"), 2)) * (
        fn.LEAST(fair_fight_expression, 3)
    )
    respect_alias = respect_expression.alias("respect")

    query = (
        User.select(
            s.c.time_added,
            s.c.battlescore,
            User.tid,
            User.name,
            User.level,
            User.last_refresh,
            User.faction_id,
            User.last_action,
            Faction.name,
            fair_fight_alias,
            respect_alias,
        )
        .join(s, on=(User.tid == s.c.tid_id))
        .join(Faction, JOIN.LEFT_OUTER, on=(Faction.tid == User.faction_id))
        .where(User.level.is_null(False))
        .limit(limit)
    )

    if minimum_level == maximum_level:
        query = query.where(User.level == maximum_level)
    else:
        if minimum_level != 1:
            query = query.where(User.level >= minimum_level)
        if maximum_level != 100:
            query = query.where(User.level <= maximum_level)

    if is_factionless or is_inactive:
        # For these options, it is important for user data to be up-to-date to ensure
        # invalid results aren't returned. Skipping this could cause the data to show
        # members who are no longer inactive or have joined a faction.

        MAX_INTERVAL_DAYS = 90
        MIN_FRACTION = 0.3
        MAX_INTERVAL_SECONDS = MAX_INTERVAL_DAYS * 24 * 3600

        seconds_since_activity = db.extract_date("epoch", fn.NOW() - User.last_action)
        fraction_of_max = fn.LEAST(1.0, fn.GREATEST(MIN_FRACTION, seconds_since_activity / MAX_INTERVAL_SECONDS))

        query = query.where(
            User.last_refresh >= fn.NOW() - fn.MAKE_INTERVAL(0, 0, 0, 0, 0, 0, fraction_of_max * MAX_INTERVAL_SECONDS)
        )

    if is_factionless:
        query = query.where((User.faction_id == 0) | (User.faction_id.is_null(True)))
    if is_inactive:
        query = query.where(
            (User.last_action <= datetime.datetime.utcnow() - datetime.timedelta(days=30))
            & (User.last_refresh >= datetime.datetime.utcnow() - datetime.timedelta(days=21))
        )

    if sort_order == "recently-updated":
        query = query.order_by(s.c.time_added.desc())
    elif sort_order == "highest-respect":
        query = query.order_by(respect_alias.desc(), s.c.time_added.desc())
    elif sort_order == "random":
        query = query.order_by(fn.Random())

    return (
        [
            {
                "time_added": int(target.stat.time_added.timestamp()),
                "stat_score": int(target.stat.battlescore),
                "fair_fight": float(round(target.fair_fight, 2)),
                "respect": float(round(target.respect, 2)),
                "target": {
                    "ID": target.tid,
                    "name": target.name,
                    "faction": (
                        {
                            "ID": target.faction.tid,
                            "name": target.faction.name,
                        }
                        if target.faction is not None
                        else None
                    ),
                    "last_action": int(target.last_action.timestamp()),
                    "last_refresh": int(target.last_refresh.timestamp()),
                },
            }
            for target in query
        ],
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
