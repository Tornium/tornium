# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json
import time

from controllers.api.decorators import *
from models.faction import Faction
from models.factionmodel import FactionModel
from models.servermodel import ServerModel
from models.user import User
import tasks
import utils


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:bot", "bot:admin"})
def forward_assist(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    assist_key = f'tornium:assist-ratelimit:{kwargs["user"].tid}'
    user = User(kwargs["user"].tid)
    target = User(data.get("target_tid"))

    if user.tid == target.tid:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The target was the same as the requesting user.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    target_faction = Faction(target.factiontid)
    servers_forwarded = []

    server: ServerModel
    for server in ServerModel.objects(assistchannel__ne=0):
        if server.config.get("assists") in (0, None) or server.assistschannel == 0:
            continue
        elif server.assist_mod == 1 and user.factionid not in server.assist_factions:
            continue
        elif server.assist_mod == 2 and user.factionid in server.assist_factions:
            continue

        data = {
            "embeds": [
                {
                    "title": "Assist Request",
                    "description": f"An assist request has been forwarded to {server.name} by {user.name} [{user.tid}].",
                    "fields": [
                        {
                            "name": "User",
                            "value": f"{target.name} [{target.tid}]",
                            "inline": True,
                        },
                        {
                            "name": "User Level",
                            "value": f"Level {target.level}",
                            "inline": True,
                        },
                        {
                            "name": "Faction",
                            "value": "Unknown"
                            if target_faction is None
                            else f"{target_faction.name} [{target_faction.tid}]",
                            "inline": True,
                        },
                        {
                            "name": "Requesting User",
                            "value": f"{user.name} [{user.tid}]",
                            "inline": True,
                        },
                        {
                            "name": "Requesting Faction",
                            "value": f"{utils.first(FactionModel.objects(tid=user.factionid)).name} [{user.factionid}]",
                            "inline": True,
                        },
                    ],
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "footer": {
                        "text": f"{round(time.time() - kwargs['start_time'], 2)} seconds"
                    },
                }
            ],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Attack Link",
                            "url": f"https://www.torn.com/loader.php?sid=attack&user2ID={target.tid}",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Profile",
                            "url": f"https://www.torn.com/profiles.php?XID={target.tid}",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Faction",
                            "url": f"https://www.torn.com/factions.php?step=profile&ID={target.factiontid}#/",
                        },
                    ],
                },
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Requesting User",
                            "url": f"https://www.torn.com/profiles.php?XID={user.tid}",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Requesting Faction",
                            "url": f"https://www.torn.com/factions.php?step=profile&ID={user.factionid}#/",
                        },
                    ],
                },
            ],
        }

        try:
            tasks.discordpost(
                f"channels/{server.assistschannel}/messages", data, dev=True
            )
        except utils.DiscordError as e:
            continue
        except utils.NetworkingError as e:
            continue

        servers_forwarded.append(server)

    return (
        jsonify(
            {
                "code": 1,
                "name": "OK",
                "message": "Server request was successful.",
                "servers_forwarded": len(servers_forwarded),
                "latency": time.time() - kwargs["start_time"],
            }
        ),
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )
