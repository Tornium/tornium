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
import random

from flask import jsonify, request
from mongoengine.queryset import QuerySet
from mongoengine.queryset.visitor import Q

import utils
from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.faction import Faction
from models.factionmodel import FactionModel
from models.statmodel import StatModel
from models.user import User
from models.usermodel import UserModel


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:stats"})
def generate_chain_list(*args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    variance = request.args.get("variance") if request.args.get("variance") is not None else 0.01
    ff = request.args.get("ff") if request.args.get("ff") is not None else 3

    if type(variance) not in (float, int) and (not variance.isdigit() or float(variance) < 0 or float(variance) > 0.1):
        return make_exception_response(
            "1000",
            key,
            details={"message": "An invalid variance has been provided."},
        )
    elif type(ff) not in (float, int) and (not ff.isdigit() or float(ff) < 1 or float(ff) > 3):
        return make_exception_response(
            "1000",
            key,
            details={"message": "An invalid FF has been provided."},
        )
    elif kwargs["user"].battlescore == 0:
        return make_exception_response(
            "0000",
            key,
            details={"message": "User does not have a stat score stored in the database."},
        )

    ff = float(ff)
    variance = float(variance)

    if ff == 3:
        variance = 0

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

    if ff == 3:
        stat_entries: QuerySet = StatModel.objects(
            (Q(globalstat=True) | Q(addedid=kwargs["user"].tid) | Q(addedfactiontid=kwargs["user"].factionid))
            & Q(battlescore__gte=(0.375 * kwargs["user"].battlescore * (ff - 1)))
            & Q(battlescore__lte=(0.375 * kwargs["user"].battlescore * 2.4))
        )
    else:
        stat_entries: QuerySet = StatModel.objects(
            (Q(globalstat=True) | Q(addedid=kwargs["user"].tid) | Q(addedfactiontid=kwargs["user"].factionid))
            & Q(battlescore__gte=(0.375 * kwargs["user"].battlescore * (ff - variance - 1)))
            & Q(battlescore__lte=(0.375 * kwargs["user"].battlescore * (ff - +variance - 1)))
        )

    stat_entries: list = list(set(stat_entries.all().values_list("tid")))
    random.shuffle(stat_entries)
    jsonified_stat_entries = []

    targets = {}
    targets_updated = 0

    for stat_entry in stat_entries:
        stat: StatModel = (
            StatModel.objects(
                Q(tid=stat_entry)
                & (Q(globalstat=True) | Q(addedid=kwargs["user"].tid) | Q(addedfactiontid=kwargs["user"].factionid))
            )
            .order_by("-timeadded")
            .first()
        )

        if stat.battlescore > kwargs["user"].battlescore:
            continue

        if stat_entry in targets:
            target = targets[stat_entry]
        else:
            target = User(tid=stat.tid)

            if targets_updated <= 50:
                try:
                    if target.refresh(key=kwargs["key"], minimize=True):
                        targets_updated += 1
                except utils.TornError:
                    if utils.now() - target.last_refresh <= 2592000:  # One day
                        pass
                    else:
                        continue
                except utils.NetworkingError as e:
                    if e.code == 408:
                        if utils.now() - target.last_refresh <= 2592000:  # One day
                            pass
                        else:
                            continue
                    else:
                        continue

        target_ff = 1 + 8 / 3 * (stat.battlescore / kwargs["user"].battlescore)

        if target_ff > 3:
            target_ff = 3
        if target.level == 0:
            continue

        try:
            base_respect = round((math.log(target.level) + 1) / 4, 2)
        except ValueError:
            continue

        jsonified_stat_entries.append(
            {
                "statid": stat.statid,
                "tid": stat.tid,
                "battlescore": stat.battlescore,
                "timeadded": stat.timeadded,
                "ff": target_ff,
                "respect": round(base_respect * target_ff, 2),
                "user": {
                    "tid": target.tid,
                    "name": target.name,
                    "username": f"{target.name} [{target.tid}]",
                    "level": target.level,
                    "last_refresh": target.last_refresh,
                    "factionid": target.factiontid,
                    "status": target.status,
                    "last_action": target.last_action,
                },
            }
        )

    return (
        jsonify(
            {
                "ff": ff,
                "variance": variance,
                "data": jsonified_stat_entries,
            }
        ),
        200,
        api_ratelimit_response(key),
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:stats"})
def get_stat_user(tid, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    stat_entries: QuerySet = (
        StatModel.objects(
            Q(tid=tid)
            & (Q(globalstat=True) | Q(addedid=kwargs["user"].tid) | Q(addedfactiontid=kwargs["user"].factionid))
        )
        .order_by("-statid")
        .exclude("tid")
        .all()
    )

    data = {"user": {}, "stat_entries": {}}

    user = User(tid)
    user.refresh(key=kwargs["user"].key)

    faction = Faction(user.factiontid)

    data["user"] = {
        "tid": user.tid,
        "name": user.name,
        "level": user.level,
        "last_refresh": user.last_refresh,
        "discord_id": user.discord_id,
        "faction": {"tid": faction.tid, "name": faction.name},
        "status": user.status,
        "last_action": user.last_action,
    }

    factions = {}
    added_users = {}

    stat_entry: StatModel
    for stat_entry in stat_entries:
        if stat_entry.addedfactiontid == 0:
            faction = None
        elif str(stat_entry.addedfactiontid) in factions:
            faction = factions[str(stat_entry.addedfactiontid)]
        else:
            faction_db: FactionModel = FactionModel.objects(tid=stat_entry.addedfactiontid).first()

            if faction_db is None:
                faction = None
                factions[str(stat_entry.addedfactiontid)] = None
            else:
                faction = {
                    "name": faction_db.name,
                    "respect": faction_db.respect,
                    "capacity": faction_db.capacity,
                    "leader": faction_db.leader,
                    "coleader": faction_db.coleader,
                }
                factions[str(stat_entry.addedfactiontid)] = faction

        if stat_entry.addedid == 0:
            added_user = None
        elif str(stat_entry.addedid) in added_users:
            added_user = added_users[str(stat_entry.addedid)]
        else:
            added_user_db: UserModel = UserModel.objects(tid=stat_entry.addedid).first()

            if added_user_db is None:
                added_user = None
                added_users[str(stat_entry.addedid)] = None
            else:
                added_user = {
                    "name": added_user_db.name,
                }
                added_users[str(stat_entry.addedid)] = added_user

        data["stat_entries"][stat_entry.statid] = {
            "stat_score": stat_entry.battlescore,
            "timeadded": stat_entry.timeadded,
            "addeduser": added_user,
            "addedid": stat_entry.addedid,
            "addedfaction": faction,
            "addedfactiontid": stat_entry.addedfactiontid,
            "globalstat": stat_entry.globalstat,
        }

    return (jsonify(data), 200, api_ratelimit_response(key))
