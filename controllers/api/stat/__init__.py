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

import random

from flask import jsonify, request
from mongoengine.queryset import QuerySet
from mongoengine.queryset.visitor import Q

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

    defender_stats = request.args.get("dstats") if request.args.get("dstats") is not None else 0.75
    variance = request.args.get("variance") if request.args.get("variance") is not None else 0.01

    if kwargs["user"].battlescore == 0:
        return make_exception_response(
            "0000",
            key,
            details={"message": "User does not have a stat score stored in the database."},
        )

    stat_entries = StatModel.objects(
        (Q(globalstat=True) | Q(addedid=kwargs["user"].tid) | Q(addedfactiontid=kwargs["user"].factionid))
        & Q(battlescore__gte=(kwargs["user"]["battlescore"] * (defender_stats - variance)))
        & Q(battlescore__lte=(kwargs["user"]["battlescore"] * (defender_stats + variance)))
    )
    stat_entries = list(set(stat_entries.all().values_list("tid")))
    random.shuffle(stat_entries)
    jsonified_stat_entires = []

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

        if stat_entry in targets:
            user = targets[stat_entry]
        else:
            user = User(tid=stat.tid)

            if targets_updated <= 50:
                if user.refresh(key=kwargs["user"].key):
                    targets_updated += 1

        jsonified_stat_entires.append(
            {
                "statid": stat.statid,
                "tid": stat.tid,
                "battlescore": stat.battlescore,
                "timeadded": stat.timeadded,
                "user": {
                    "tid": user.tid,
                    "name": user.name,
                    "username": f"{user.name} [{user.tid}]",
                    "level": user.level,
                    "last_refresh": user.last_refresh,
                    "factionid": user.factiontid,
                    "status": user.status,
                    "last_action": user.last_action,
                },
            }
        )

    return (
        jsonify(
            {
                "defender_stats": defender_stats,
                "variance": variance,
                "data": jsonified_stat_entires,
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
