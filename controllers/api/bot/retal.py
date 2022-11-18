# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json
import random

from controllers.api.decorators import *
from models.factionmodel import FactionModel
from models.servermodel import ServerModel


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def faction_retal_channel(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = data.get("guildid")
    factiontid = data.get("factiontid")
    channelid = data.get("channel")

    if (
        guildid in ("", None, 0)
        or not guildid.isdigit()
        or factiontid in ("", None, 0)
        or not factiontid.isdigit()
        or channelid in ("", None, 0)
        or not channelid.isdigit()
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. A valid guild ID and channel ID are required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    guildid = int(guildid)
    factiontid = int(factiontid)
    channelid = int(channelid)

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. The guild ID could not be matched with a server "
                    "in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif factiontid not in guild.factions:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The faction is not valid for this server.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    faction: FactionModel = FactionModel.objects(tid=factiontid).first()

    if faction is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownFaction",
                    "message": "Server failed to fulfill the request. The faction ID could not be matched with a "
                    "faction in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif faction.guild != guildid:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The faction's server could not be matched with "
                    "this server.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    if str(factiontid) in guild.retal_config:
        guild.retal_config[str(factiontid)] = channelid
    else:
        guild.retal_config = {f"{factiontid}": channelid}

    guild.save()

    return (
        jsonify(guild.retal_config),
        200,
        {
            "X-RateLimit-Limit": 250,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )
