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
from mongoengine.queryset import QuerySet
from mongoengine.queryset.visitor import Q
from tornium_celery.tasks.user import update_user
from tornium_commons.models import FactionModel, StatModel, UserModel

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

    difficulty = request.args.get("difficulty", 2)
    sort = request.args.get("sort", "timestamp")
    limit = request.args.get("limit", 10)

    try:
        difficulty = int(difficulty)
        limit = int(limit)
    except ValueError:
        return make_exception_response(
            "1000", key, details={"message": "Illegal parameter type. Must be a float or integer."}
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

    if difficulty < 4:
        min_ff = _DIFFICULTY_MAP[difficulty][0]
        max_ff = _DIFFICULTY_MAP[difficulty][1]

        stat_entries: typing.Union[QuerySet, list] = StatModel.objects(
            (Q(globalstat=True) | Q(addedid=kwargs["user"].tid) | Q(addedfactiontid=kwargs["user"].factionid))
            & Q(battlescore__gte=(0.375 * kwargs["user"].battlescore * (min_ff - 1)))
            & Q(battlescore__lte=(0.375 * kwargs["user"].battlescore * (max_ff - 1)))
        )
    else:
        min_ff = _DIFFICULTY_MAP[difficulty][0]

        stat_entries: typing.Union[QuerySet, list] = StatModel.objects(
            (Q(globalstat=True) | Q(addedid=kwargs["user"].tid) | Q(addedfactiontid=kwargs["user"].factionid))
            & Q(battlescore__gte=(0.375 * kwargs["user"].battlescore * (min_ff - 1)))
            & Q(battlescore__lte=(0.375 * kwargs["user"].battlescore * 2.4))
        )

    if sort == "timestamp":
        stat_entries_sorted = stat_entries.order_by("-timeadded")
    elif sort == "random":
        stat_entries_sorted = list(stat_entries.aggregate(pipeline=[{"$sample": {"size": limit}}]))
    else:
        stat_entries_sorted = stat_entries

    jsonified_stat_entries = []
    targets = []

    # stat_entry: typing.Union[StatModel, dict]
    for stat_entry in stat_entries_sorted:
        if len(jsonified_stat_entries) >= limit:
            break

        if type(stat_entry) == StatModel:
            stat_dict = dict(stat_entry.to_mongo())
        else:
            stat_dict = stat_entry

        if stat_dict["tid"] in targets:
            continue

        target: typing.Optional[UserModel] = UserModel.objects(tid=stat_dict["tid"]).first()

        if target is None:
            try:
                update_user(kwargs["user"].key, tid=stat_dict["tid"])
            except Exception as e:
                print(e)

            continue

        # Get latest viewable stat entry for the specified user
        stat_entry = stat_entries.filter(tid=stat_entry["tid"]).order_by("-timeadded").first()

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
                "statid": str(stat_entry.id),
                "tid": stat_entry.tid,
                "battlescore": stat_entry.battlescore,
                "timeadded": stat_entry.timeadded,
                "ff": target_ff,
                "respect": round(base_respect * target_ff, 2),
                "user": {
                    "tid": target.tid,
                    "name": target.name,
                    "username": f"{target.name} [{target.tid}]",
                    "level": target.level,
                    "last_refresh": target.last_refresh,
                    "factionid": target.factionid,
                    "status": target.status,
                    "last_action": target.last_action,
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
def get_stat_user(tid, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    stat_entries: QuerySet = (
        StatModel.objects(
            Q(tid=tid)
            & (Q(globalstat=True) | Q(addedid=kwargs["user"].tid) | Q(addedfactiontid=kwargs["user"].factionid))
        )
        .order_by("-timeadded")
        .exclude("tid")
        .all()
    )

    data = {"user": {}, "stat_entries": {}}

    update_user(kwargs["user"].key, tid=tid).get()
    user: UserModel = UserModel.objects(tid=tid).no_cache().first()

    if user is None:
        return make_exception_response("1100", key)

    if user.factionid != 0:
        faction = FactionModel.objects(tid=user.factionid).first()
    else:
        faction = None

    data["user"] = {
        "tid": user.tid,
        "name": user.name,
        "level": user.level,
        "last_refresh": user.last_refresh,
        "discord_id": user.discord_id,
        "faction": {"tid": faction.tid, "name": faction.name} if faction is not None else {"tid": 0, "name": "None"},
        "status": user.status,
        "last_action": user.last_action,
    }

    stat_entry: StatModel
    for stat_entry in stat_entries:
        data["stat_entries"][str(stat_entry.id)] = {
            "stat_score": stat_entry.battlescore,
            "timeadded": stat_entry.timeadded,
            "globalstat": stat_entry.globalstat,
        }

    return (jsonify(data), 200, api_ratelimit_response(key))
