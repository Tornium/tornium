# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json

from controllers.api.decorators import *
from models.factionmodel import FactionModel
from models.positionmodel import PositionModel
from models.servermodel import ServerModel


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:faction", "faction:admin"})
def get_positions(*args, **kwargs):
    client = redisdb.get_redis()
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = request.args.get("guildid")
    factiontid = request.args.get("factiontid")

    if (
        guildid not in (None, 0, "")
        and factiontid not in (None, 0, "")
        and guildid.isdigit()
        and factiontid.isdigit()
    ):
        guildid = int(guildid)
        factiontid = int(factiontid)

        if kwargs["user"].factionid != factiontid or not kwargs["user"].factionaa:
            guild: ServerModel = ServerModel.objects(sid=guildid).first()

            if guild is None:
                return (
                    jsonify(
                        {
                            "code": 1001,
                            "name": "UnknownGuild",
                            "message": "Server failed to locate the requested guild.",
                        }
                    ),
                    400,
                    {
                        "X-RateLimit-Limit": 250,
                        "X-RateLimit-Remaining": client.get(key),
                        "X-RateLimit-Reset": client.ttl(key),
                    },
                )
            elif kwargs["user"].tid not in guild.admins:
                return (
                    jsonify(
                        {
                            "code": 4020,
                            "name": "InsufficientDiscordPermissions",
                            "message": "Server failed to fulfill the request. The user is not an admin in the provided guild.",
                        }
                    ),
                    403,
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
                            "message": "Server failed to fulfill the request. The faction is not list as in the guild.",
                        }
                    ),
                    403,
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
                            "name": "GeneralError",
                            "message": "Server failed to locate the requested faction.",
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
                            "message": "Server failed to fulfill the request. The faction is not list as in the guild.",
                        }
                    ),
                    403,
                    {
                        "X-RateLimit-Limit": 250,
                        "X-RateLimit-Remaining": client.get(key),
                        "X-RateLimit-Reset": client.ttl(key),
                    },
                )
        else:
            faction: FactionModel = FactionModel.objects(
                tid=kwargs["user"].factionid
            ).first()
    else:
        if kwargs["user"].factionid == 0:
            return (
                jsonify(
                    {
                        "code": 0,
                        "name": "GeneralError",
                        "message": "Server failed to fulfill the request. The user is not in a faction.",
                    }
                ),
                400,
                {
                    "X-RateLimit-Limit": 250,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )
        elif not kwargs["user"].factionaa:
            return (
                jsonify(
                    {
                        "code": 4005,
                        "name": "InsufficientFactionPermissions",
                        "message": "Server failed to fulfill the request. The provided authentication code was not sufficient for an AA level request.",
                    }
                ),
                403,
                {
                    "X-RateLimit-Limit": 250,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )

        faction: FactionModel = FactionModel.objects(
            tid=kwargs["user"].factionid
        ).first()

    if faction is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownFaction",
                    "message": "Server failed to fulfill the request. No faction matched the user's faction.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif utils.now() - faction.last_members >= 86400:  # one day
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "ExpiredData",
                    "message": "Server failed to fulfill the request. The data hasn't been updated sufficiently recently.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    positions = PositionModel.objects(factiontid=faction.tid)

    if positions.count() == 0:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. There are no positions stored in the database for the faction.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    positions_data = []

    position: PositionModel
    for position in positions:
        position_data = json.loads(position.to_json())
        position_data["_id"] = str(position.name)
        positions_data.append(position_data)

    return (
        jsonify({"positions": positions_data}),
        200,
        {
            "X-RateLimit-Limit": 250,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )
