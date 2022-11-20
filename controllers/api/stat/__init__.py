# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from mongoengine.queryset.visitor import Q

from controllers.api.decorators import *
from models.statmodel import StatModel
from models.user import User


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:stats"})
def generate_chain_list(*args, **kwargs):
    # curl -H "Authorization: Basic " localhost:8000/api/stat
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    defender_stats = (
        request.args.get("dstats") if request.args.get("dstats") is not None else 0.75
    )
    variance = (
        request.args.get("variance")
        if request.args.get("variance") is not None
        else 0.01
    )

    if kwargs["user"].battlescore == 0:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "General Error",
                    "message": "Server failed the fulfill the request. There was no battle stats scored for the user but the "
                    "battle stats are required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    stat_entries = StatModel.objects(
        (
            Q(globalstat=True)
            | Q(addedid=kwargs["user"].tid)
            | Q(addedfactiontid=kwargs["user"].factionid)
        )
        & Q(
            battlescore__gte=(
                kwargs["user"]["battlescore"] * (defender_stats - variance)
            )
        )
        & Q(
            battlescore__lte=(
                kwargs["user"]["battlescore"] * (defender_stats + variance)
            )
        )
    )
    stat_entries = list(stat_entries.all().values_list("statid"))
    random.shuffle(stat_entries)
    jsonified_stat_entires = []
    jsonified_stat_ids = []

    for stat_entry in stat_entries:
        if len(jsonified_stat_entires) >= 10:
            break

        stat: StatModel = StatModel.objects(statid=stat_entry).first()

        if stat.tid in jsonified_stat_ids:
            continue

        user = User(tid=stat.tid)
        user.refresh(key=kwargs["user"].key)

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
        jsonified_stat_ids.append(stat.tid)

    return (
        jsonify(
            {
                "defender_stats": defender_stats,
                "variance": variance,
                "data": jsonified_stat_entires,
            }
        ),
        200,
        {
            "X-RateLimit-Limit": 250,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:stats"})
def get_stat_user(tid, *args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    limit = request.args.get("limit") if request.args.get("limit") is not None else 10

    stat_entries = (
        StatModel.objects(
            (
                Q(globalstat=True)
                | Q(addedid=kwargs["user"].tid)
                | Q(addedfactiontid=kwargs["user"].factionid)
            )
            & Q(tid=tid)
        )
        .order_by("-statid")[:limit]
        .all()
    )
    jsonified_stat_entries = []
    users = []

    for stat_entry in stat_entries:
        if stat_entry.tid in users:
            continue
        else:
            users.append(stat_entry.tid)

        user = User(stat_entry.tid)
        user.refresh(key=kwargs["user"].key)

        jsonified_stat_entries.append(
            {
                "statid": stat_entry.statid,
                "tid": stat_entry.tid,
                "battlescore": stat_entry.battlescore,
                "timeadded": stat_entry.addedid,
            }
        )

    return (
        jsonify({"limit": limit, "data": jsonified_stat_entries}),
        200,
        {
            "X-RateLimit-Limit": 250,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )
