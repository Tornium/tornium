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

from flask import jsonify, request
from peewee import DoesNotExist
from tornium_celery.tasks.user import update_user
from tornium_commons.db_connection import db
from tornium_commons.models import Stat, User

from controllers.api.v1.decorators import authentication_required, ratelimit
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response

_DIFFICULTY_MAP = {
    0: (1.25, 1.75),
    1: (1.75, 2),
    2: (2, 2.25),
    3: (2.25, 2.5),
    4: (2.5, 3.4),  # max_ff is actually 3
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
    #     4      |  2.5   |  3.4   |  Very Hard  |
    #
    # Max FF of difficulty 4 is indicated as 3.4 but is 3
    # In the equation, 3x FF is equivalent to times 2.4 which is 3.4 - 1

    parameters = []

    min_ff = _DIFFICULTY_MAP[difficulty][0]
    max_ff = _DIFFICULTY_MAP[difficulty][1]

    parameters.append(kwargs["user"].faction_id)
    parameters.append(int(0.375 * kwargs["user"].battlescore * (min_ff - 1)))
    parameters.append(int(0.375 * kwargs["user"].battlescore * (max_ff - 1)))

    # Paramter order
    # 0 = added faction
    # 1 = min battlescore
    # 2 = max battlescore
    # 3 = limit

    if sort == "timestamp":
        query = 'select "t1"."id", "t1"."tid_id", "t1"."time_added", "t1"."battlescore", "t2"."name", "t2"."level", "t2"."last_refresh", "t2"."faction_id", "t2"."status", "t2"."last_action" from (select * from (select distinct on ("t1"."tid_id") * from "stat" as "t1" where ("t1"."added_group" = 0) or ("t1"."added_group" = %s) order by "t1"."tid_id", "t1"."time_added" desc) t1 where ("t1"."battlescore" >= %s) and ("t1"."battlescore" <= %s)) t1 join "user" as "t2" on "t2"."tid" = "t1"."tid_id" where "t2"."level" is not null order by "t1"."time_added" desc limit %s'
    elif sort == "random":
        query = 'select "t1"."id", "t1"."tid_id", "t1"."time_added", "t1"."battlescore", "t2"."name", "t2"."level", "t2"."last_refresh", "t2"."faction_id", "t2"."status", "t2"."last_action" from (select * from (select distinct on ("t1"."tid_id") * from "stat" as "t1" where ("t1"."added_group" = 0) or ("t1"."added_group" = %s) order by "t1"."tid_id", "t1"."time_added" desc) t1 where ("t1"."battlescore" >= %s) and ("t1"."battlescore" <= %s)) t1 join "user" as "t2" on "t2"."tid" = "t1"."tid_id" where "t2"."level" is not null order by random() limit %s'
    else:  # Sorted by respect
        query = f'select "t1"."id", "t1"."tid_id", "t1"."time_added", "t1"."battlescore", "t2"."name", "t2"."level", "t2"."last_refresh", "t2"."faction_id", "t2"."status", "t2"."last_action" from (select * from (select distinct on ("t1"."tid_id") * from "stat" as "t1" where ("t1"."added_group" = 0) or ("t1"."added_group" = %s) order by "t1"."tid_id", "t1"."time_added" desc) t1 where ("t1"."battlescore" >= %s) and ("t1"."battlescore" <= %s)) t1 join "user" as "t2" on "t2"."tid" = "t1"."tid_id" where "t2"."level" is not null order by ((log("t2"."level") + 1) / 4 * greatest(1 + 8 / 3 * ("t1"."battlescore" / {int(kwargs["user"].battlescore)}), 3)) desc, "t1"."time_added" desc limit %s'
        # TODO: Make the query store the FF and respect in the query result

    # Query response order
    # 0 = stat.id
    # 1 = stat.tid_id
    # 2 = stat.time_added
    # 3 = stat.battlescore
    # 4 = stat.tid.name
    # 5 = stat.tid.level
    # 6 = stat.tid.last_refresh
    # 7 = stat.tid.faction_id
    # 8 = stat.tid.status
    # 9 = stat.tid.last_action

    parameters.append(limit)
    jsonified_stat_entries = []

    for stat_entry in db().execute_sql(query, parameters):
        target_ff = round(1 + 8 / 3 * (stat_entry[3] / kwargs["user"].battlescore), 2)

        if target_ff > 3:
            target_ff = 3
        if stat_entry[1] is None or stat_entry[5] in (0, None):
            continue

        try:
            base_respect = round((math.log(stat_entry[5]) + 1) / 4, 2)
        except ValueError:
            continue

        jsonified_stat_entries.append(
            {
                "statid": stat_entry[0],
                "tid": stat_entry[1],
                "battlescore": stat_entry[3],
                "timeadded": stat_entry[2].timestamp(),
                "ff": target_ff,
                "respect": round(base_respect * target_ff, 2),
                "user": {
                    "tid": stat_entry[1],
                    "name": stat_entry[4],
                    "username": f"{stat_entry[4]} [{stat_entry[1]}]",
                    "level": stat_entry[5],
                    "last_refresh": stat_entry[6].timestamp() if stat_entry[6] is not None else None,
                    "factionid": stat_entry[7],
                    "status": stat_entry[8],
                    "last_action": stat_entry[9].timestamp(),
                },
            }
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


@authentication_required
@ratelimit
def get_stat_user(tid: int, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    stat_entries = (
        Stat.select()
        .where(((Stat.added_group == 0) | (Stat.added_group == kwargs["user"].faction_id)) & (Stat.tid == tid))
        .order_by(-Stat.time_added)
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
            "timeadded": stat_entry.time_added.timestamp(),
        }

    return jsonify(data), 200, api_ratelimit_response(key)
