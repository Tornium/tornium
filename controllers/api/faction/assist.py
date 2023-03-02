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
import typing

from flask import jsonify, request

from tornium_commons import rds
from tornium_commons.models import FactionModel, ServerModel, UserModel
from tornium_celery.tasks.api import discordpost
from tornium_celery.tasks.user import update_user

import utils
from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:bot", "bot:admin"})
def forward_assist(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = rds()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    assist_key = f'tornium:assist-ratelimit:{kwargs["user"].tid}'

    if data.get("target_tid") is None:
        return make_exception_response("1100", key, redis_client=client)

    target_data = update_user(key=kwargs["user"].key, tid=data.get("target_tid"))

    if client.get(assist_key) is not None:
        return make_exception_response("4291", key, redis_client=client)
    else:
        client.set(assist_key, 1)
        client.expire(assist_key, 30)

    if target_data["player_id"] == data.get("target_tid"):
        return make_exception_response(
            "0000",
            key,
            details={"message": "The target was the same as the requesting user."},
            redis_client=client,
        )

    target: UserModel = UserModel.objects(tid=target_data["player_id"]).first()

    if target is None:
        return make_exception_response("1100", key, redis_client=client)

    target_faction: typing.Optional[FactionModel]

    if target.factionid != 0:
        target_faction = FactionModel.objects(tid=target.factionid).first()

        if target_faction is None:
            return make_exception_response("1102", key, redis_client=client)
    else:
        target_faction = None

    servers_forwarded = []

    server: ServerModel
    for server in ServerModel.objects(assistchannel__ne=0):
        if server.assistschannel == 0:
            continue
        elif server.assist_mod == 1 and kwargs["user"].factiontid not in server.assist_factions:
            continue
        elif server.assist_mod == 2 and kwargs["user"].factiontid in server.assist_factions:
            continue

        data = {
            "embeds": [
                {
                    "title": "Assist Request",
                    "description": f"An assist request has been forwarded to {server.name} by "
                    f"{kwargs['user'].name} [{kwargs['user'].tid}].",
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
                            "value": f"{kwargs['user'].name} [{kwargs['user'].tid}]",
                            "inline": True,
                        },
                        {
                            "name": "Requesting Faction",
                            "value": f"{FactionModel.objects(tid=kwargs['user'].factiontid).first().name} [{kwargs['user'].factiontid}]",
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
                            "url": f"https://www.torn.com/factions.php?step=profile&ID={target.factionid}#/",
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
                            "url": f"https://www.torn.com/profiles.php?XID={kwargs['user'].tid}",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Requesting Faction",
                            "url": f"https://www.torn.com/factions.php?step=profile&ID={kwargs['user'].factiontid}#/",
                        },
                    ],
                },
            ],
        }

        try:
            discordpost.delay(f"channels/{server.assistschannel}/messages", data)
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
