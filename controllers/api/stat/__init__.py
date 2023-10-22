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

import math
import operator
import typing

from flask import jsonify, request
from peewee import DoesNotExist, fn
from tornium_celery.tasks.user import update_user
from tornium_commons.models import Stat, User

from controllers.api.decorators import authentication_required, ratelimit
from controllers.api.utils import api_ratelimit_response, make_exception_response

_DIFFICULTY_MAP = {
    0: (1.25, 1.75),
    1: (1.75, 2),
    2: (2, 2.25),
    3: (2.25, 2.5),
    4: (2.5, 3),
}


@authentication_required
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

    # f = fair fight
    # v = variance
    # d = defender's stat score
    # a = attacker's stat score
    #
    # f +- v = 1 + 8/3 * d/a
    # 0.375 * a * (f +- v - 1) = d
    #
    # f = 11/3 is equal ratio of d/a
    # f = 17/5 is 9/10 ratio of d/a

    # Difficulty | Min FF | Max FF |     Name    |
    #     0      |  1.25  |  1.75  |  Very Easy  |
    #     1      |  1.75  |   2    |    Easy     |
    #     2      |   2    |  2.25  |   Medium    |
    #     3      |  2.25  |  2.5   |    Hard     |
    #     4      |  2.5   |   3    |  Very Hard  |

    stat_entries: typing.Iterable[Stat]
    if difficulty < 4:
        min_ff = _DIFFICULTY_MAP[difficulty][0]
        max_ff = _DIFFICULTY_MAP[difficulty][1]

        stat_entries = Stat.select().where(
            (
                (Stat.global_stat == True)
                | (Stat.added_tid == kwargs["user"].tid)
                | (Stat.added_faction_tid == kwargs["user"].faction.tid)
            )
            & (Stat.battlescore >= 0.375 * kwargs["user"].battlescore * (min_ff - 1))
            & (Stat.battlescore <= 0.375 * kwargs["user"].battlescore * (max_ff - 1))
        )
    else:
        min_ff = _DIFFICULTY_MAP[difficulty][0]

        stat_entries = Stat.select().where(
            (
                (Stat.global_stat == True)
                | (Stat.added_tid == kwargs["user"].tid)
                | (Stat.added_faction_tid == kwargs["user"].faction.tid)
            )
            & (Stat.battlescore >= 0.375 * kwargs["user"].battlescore * (min_ff - 1))
            & (Stat.battlescore <= 0.375 * kwargs["user"].battlescore * 2.4)
        )

    if sort == "timestamp":
        stat_entries_sorted = stat_entries.order_by(-Stat.time_added)
    elif sort == "random":
        stat_entries_sorted = stat_entries.order_by(fn.Random())
    else:
        stat_entries_sorted = stat_entries

    jsonified_stat_entries = []
    targets = []

    stat_entry: typing.Union[Stat, dict]
    for stat_entry in stat_entries_sorted:
        if len(jsonified_stat_entries) >= limit and sort != "respect":
            break
        elif stat_entry.tid in targets:
            continue

        try:
            target: User = User.get_by_id(stat_entry.tid)
        except DoesNotExist:
            try:
                update_user.delay(kwargs["user"].key, tid=stat_entry.tid)
            except Exception as e:
                print(e)

            continue

        # Get latest viewable stat entry for the specified user
        stat_entry = (
            Stat.select()
            .where(
                (
                    (Stat.global_stat == True)
                    | (Stat.added_tid == kwargs["user"].tid)
                    | (Stat.added_faction_tid == kwargs["user"].faction.tid)
                )
                & (Stat.tid == stat_entry.tid)
            )
            .order_by(-Stat.time_added)
            .get()
        )

        targets.append(stat_entry.tid)
        target_ff = round(1 + 8 / 3 * (stat_entry.battlescore / kwargs["user"].battlescore), 2)

        if target_ff > 3:
            target_ff = 3
        if target is None or target.level == 0:
            continue

        try:
            base_respect = round((math.log(target.level) + 1) / 4, 2)
        except ValueError:
            continue

        jsonified_stat_entries.append(
            {
                "statid": str(stat_entry.get_id()),
                "tid": stat_entry.tid,
                "battlescore": stat_entry.battlescore,
                "timeadded": stat_entry.time_added.to_timestamp(),
                "ff": target_ff,
                "respect": round(base_respect * target_ff, 2),
                "user": {
                    "tid": target.tid,
                    "name": target.name,
                    "username": f"{target.name} [{target.tid}]",
                    "level": target.level,
                    "last_refresh": target.last_refresh.to_timestamp(),
                    "factionid": target.faction.tid,
                    "status": target.status,
                    "last_action": target.last_action.to_timestamp(),
                },
            }
        )

    if sort == "respect":
        jsonified_stat_entries = sorted(jsonified_stat_entries, key=operator.itemgetter("respect"), reverse=True)[
            :limit
        ]
    elif sort == "timestamp":
        jsonified_stat_entries = sorted(jsonified_stat_entries, key=operator.itemgetter("timeadded"), reverse=True)

    return (
        jsonify(
            {
                "data": jsonified_stat_entries,
            }
        ),
        200,
        api_ratelimit_response(key),
    )


@authentication_required
@ratelimit
def get_stat_user(tid: int, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    stat_entries = (
        Stat.select()
        .where(
            (
                (Stat.global_stat == True)
                | (Stat.added_tid == kwargs["user"].tid)
                | (Stat.added_faction_tid == kwargs["user"].faction.tid)
            )
            & (Stat.tid == tid)
        )
        .order_by(-Stat.time_added)
    )

    data = {"user": {}, "stat_entries": {}}

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
        "faction": {"tid": user.faction.tid, "name": user.faction.name}
        if user.faction is not None
        else {"tid": 0, "name": "None"},
        "status": user.status,
        "last_action": user.last_action,
    }

    stat_entry: Stat
    for stat_entry in stat_entries:
        data["stat_entries"][str(stat_entry.get_id())] = {
            "stat_score": stat_entry.battlescore,
            "timeadded": stat_entry.time_added.to_timestamp(),
            "globalstat": stat_entry.global_stat,
        }

    return jsonify(data), 200, api_ratelimit_response(key)
