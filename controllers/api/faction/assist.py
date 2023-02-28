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

import datetime
import json
import time

from flask import jsonify, request

import redisdb
import tasks
import tasks.api
import utils
from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.faction import Faction
from models.factionmodel import FactionModel
from models.servermodel import ServerModel
from models.user import User


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
    target.refresh(key=user.key)

    if client.get(assist_key) is not None:
        return make_exception_response("4291", key, redis_client=client)
    else:
        client.set(assist_key, 1)
        client.expire(assist_key, 30)

    if user.tid == target.tid:
        return make_exception_response(
            "0000",
            key,
            details={"message": "The target was the same as the requesting user."},
            redis_client=client,
        )

    target_faction = Faction(target.factiontid)
    servers_forwarded = []

    server: ServerModel
    for server in ServerModel.objects(assistchannel__ne=0):
        if server.assistschannel == 0:
            continue
        elif server.assist_mod == 1 and user.factiontid not in server.assist_factions:
            continue
        elif server.assist_mod == 2 and user.factiontid in server.assist_factions:
            continue

        data = {
            "embeds": [
                {
                    "title": "Assist Request",
                    "description": f"An assist request has been forwarded to {server.name} by "
                    f"{user.name} [{user.tid}].",
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
                            "value": f"{FactionModel.objects(tid=user.factiontid).first().name} [{user.factiontid}]",
                            "inline": True,
                        },
                    ],
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "footer": {"text": f"Latency: {round(time.time() - kwargs['start_time'], 2)} seconds"},
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
                            "url": f"https://www.torn.com/factions.php?step=profile&ID={user.factiontid}#/",
                        },
                    ],
                },
            ],
        }

        try:
            tasks.api.discordpost(f"channels/{server.assistschannel}/messages", data)
        except utils.DiscordError:
            continue
        except utils.NetworkingError:
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
        api_ratelimit_response(key),
    )
