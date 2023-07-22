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
import inspect
import json
import random
import time
import typing
import uuid

from celery.result import AsyncResult
from flask import jsonify, request
from mongoengine.queryset.visitor import Q
from redis.commands.json.path import Path
from tornium_celery.tasks.api import discordpost, torn_stats_get
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.formatters import bs_to_range, commas
from tornium_commons.models import (
    FactionModel,
    PersonalStatModel,
    ServerModel,
    StatModel,
    UserModel,
)

from controllers.api.utils import api_ratelimit_response, make_exception_response


def forward_assist(*args, **kwargs):
    start_ts = time.time()
    data = json.loads(request.get_data().decode("utf-8"))
    client = rds()

    user_tid = data.get("user_tid")
    target_tid = data.get("target_tid")
    smokes = data.get("smokes", 0)
    tears = data.get("tears", 0)
    heavies = data.get("heavies", 0)
    timeout = data.get("timeout")

    if user_tid is None or target_tid is None:
        return make_exception_response("1100", redis_client=client)

    try:
        user_tid = int(user_tid)
        target_tid = int(target_tid)
        smokes = int(smokes)
        tears = int(tears)
        heavies = int(heavies)

        if timeout is not None:
            timeout = int(timeout)
    except TypeError:
        return make_exception_response("1000", redis_client=client)

    user: typing.Optional[UserModel] = UserModel.objects(tid=user_tid).first()

    if user is None:
        return make_exception_response("1100", redis_client=client)

    key = f"tornium:ratelimit:{user_tid}"
    assist_lock_key = f"tornium:assists:{target_tid}:lock"

    if client.exists(assist_lock_key):
        return make_exception_response("4291", key, redis_client=client)
    else:
        client.set(assist_lock_key, int(datetime.datetime.utcnow().timestamp()) + 10, nx=True, ex=10)

    if user.factionid != 0:
        user_faction: typing.Optional[FactionModel] = FactionModel.objects(tid=user.factionid).first()

        if user_faction is None:
            return make_exception_response("1102", key, redis_client=client)
    else:
        return make_exception_response("1102", key, redis_client=client)

    call_key: str
    if user.key in ("", None):
        if user_faction is None or len(user_faction.aa_keys) == 0:
            return make_exception_response("1200", redis_client=client)

        call_key = random.choice(user_faction.aa_keys)
    else:
        call_key = user.key

    try:
        update_user(key=call_key, tid=target_tid, refresh_existing=False).get()
    except AttributeError:
        pass

    target: UserModel = UserModel.objects(tid=target_tid).no_cache().first()

    if target is None:
        return make_exception_response("1100", key, redis_client=client)

    target_faction: typing.Optional[FactionModel]

    if target.factionid != 0:
        target_faction = FactionModel.objects(tid=target.factionid).first()

        if target_faction is None:
            return make_exception_response("1102", key, redis_client=client)
    else:
        target_faction = None

    target_spy: AsyncResult = torn_stats_get.delay(
        f"spy/user/{target_tid}",
        call_key,
    )

    if target.factionid != 0 and target_faction is not None:
        if target_faction.tag in ("", None):
            content_target_faction = target_faction.name
        else:
            content_target_faction = target_faction.tag
    else:
        content_target_faction = ""

    if user.factionid != 0 and user_faction is not None:
        if user_faction.tag in ("", None):
            user_faction_str = user_faction.name
        else:
            user_faction_str = user_faction.tag
    else:
        user_faction_str = ""

    requested_types = []
    components_payload = []
    fields_payload = []

    guid = uuid.uuid4().hex

    if heavies > 0:
        requested_types.append(f"{heavies}x heavies")
        components_payload.append(
            {
                "type": 2,
                "style": 5,
                "label": "Join Heavies",
                "url": f"https://tornium.com/faction/assists/{guid}?type=heavy",
            }
        )
        fields_payload.append(
            {
                "name": "Heavies Needed",
                "value": heavies,
                "inline": False,
            }
        )

    if tears > 0:
        requested_types.append(f"{tears}x tears")
        components_payload.append(
            {
                "type": 2,
                "style": 5,
                "label": "Join Tears",
                "url": f"https://tornium.com/faction/assists/{guid}?type=tear",
            }
        )
        fields_payload.append(
            {
                "name": "Tears Needed",
                "value": tears,
                "inline": True,
            }
        )

    if smokes > 0:
        requested_types.append(f"{smokes}x smokers")
        components_payload.append(
            {
                "type": 2,
                "style": 5,
                "label": "Join Smokers",
                "url": f"https://tornium.com/faction/assists/{guid}?type=smoke",
            }
        )
        fields_payload.append(
            {
                "name": "Smokers Needed",
                "value": smokes,
                "inline": True,
            }
        )

    requested_types_str: str
    if len(requested_types) == 1:
        requested_types_str = requested_types[0]
    elif len(requested_types) == 2:
        requested_types_str = f"{requested_types[0]} and {requested_types[1]}"
    elif len(requested_types) > 2:
        requested_types_str = ", ".join(requested_types[:-1]) + ", and " + requested_types[-1]
    else:
        requested_types_str = "some help"

    timeout_str: str
    if timeout is None:
        timeout_str = ""
    else:
        timeout_str = f" The attack times out <t:{timeout}:R>."

    # target_tid | user_tid | smokes | tears | heavies
    client.set(f"tornium:assists:{guid}", f"{target_tid}|{user_tid}|{smokes}|{tears}|{heavies}", nx=True, ex=600)

    payload = {
        "content": f"Assist on {target.name} [{content_target_faction}]",
        "embeds": [
            {
                "title": f"{user.name} {user_faction_str} needs help with {target.name} [{content_target_faction}]",
                "description": f"{user.name} has requested {requested_types_str}.{timeout_str}",
                "fields": fields_payload,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            },
            {
                "title": "Additional Target Information",
                "fields": [],
                "footer": {"text": f"Latency: {round(time.time() - start_ts, 1)} second(s)"},
            },
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Join Attack",
                        "url": f"https://www.torn.com/loader2.php?sid=getInAttack&user2ID={target_tid}",
                    },
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Items",
                        "url": "https://www.torn.com/item.php",
                    },
                ],
            }
        ],
    }

    if len(components_payload) != 0:
        payload["components"].insert(
            0,
            {
                "type": 1,
                "components": components_payload,
            },
        )

    stat: StatModel = (
        StatModel.objects(
            Q(tid=target_tid) & (Q(globalstat=True) | Q(addedfactiontid=user.factionid) | Q(addedid=user_tid))
        )
        .order_by("-timeadded")
        .first()
    )

    if stat is not None:
        payload["embeds"][1]["fields"].append(
            {
                "name": "Estimated Total Stats",
                "value": commas(int(sum(bs_to_range(stat.battlescore)) / 2)),
                "inline": True,
            }
        )
        payload["embeds"][1]["fields"].append(
            {
                "name": "Stat Score Update",
                "value": f"<t:{stat.timeadded}:R>",
                "inline": True,
            }
        )

    ps: typing.Optional[PersonalStatModel] = PersonalStatModel.objects(tid=user_tid).order_by("-timestamp").first()

    if ps is not None:
        payload["embeds"][1]["description"] = inspect.cleandoc(
            f"""Xanax Used: {commas(ps.xantaken)}
            Refills Used: {commas(ps.refills)}
            Energy Drinks Drunk: {commas(ps.energydrinkused)}
            LSD Used: {commas(ps.lsdtaken)}
            SEs Used: {commas(ps.statenhancersused)}
            
            ELO: {commas(ps.elo)}
            Best Damage: {commas(ps.bestdamage)}
            Networth: {commas(ps.networth)}
            
            Personal Stat Last Update: <t:{ps.timestamp}:R>
            """  # noqa: W293
        )

    try:
        target_spy_data: dict = target_spy.get()
        ts_e = False
    except Exception:
        ts_e = True

    if not ts_e and target_spy_data["status"]:
        payload["embeds"][1]["fields"].append(
            {
                "name": "Target Strength",
                "value": commas(target_spy_data["spy"]["strength"]),
                "inline": True,
            }
        )
        payload["embeds"][1]["fields"].append(
            {
                "name": "Target Defense",
                "value": commas(target_spy_data["spy"]["defense"]),
                "inline": True,
            }
        )
        payload["embeds"][1]["fields"].append(
            {
                "name": "Target Speed",
                "value": commas(target_spy_data["spy"]["speed"]),
                "inline": True,
            }
        )
        payload["embeds"][1]["fields"].append(
            {
                "name": "Target Dexterity",
                "value": commas(target_spy_data["spy"]["dexterity"]),
                "inline": True,
            }
        )
        payload["embeds"][1]["fields"].append(
            {
                "name": "Target Total",
                "value": commas(target_spy_data["spy"]["total"]),
                "inline": True,
            }
        )
        payload["embeds"][1]["fields"].append(
            {
                "name": "Target Last Update",
                "value": f"<t:{target_spy_data['spy']['timestamp']}:R>",
                "inline": True,
            }
        )

    # TODO: Role pings

    client.json().set(f"tornium:assists:{guid}:payload", Path.root_path(), payload, nx=True)
    client.expire(f"tornium:assists:{guid}:payload", 600)

    servers_forwarded = []
    messages = []

    server: ServerModel
    for server in ServerModel.objects(assistchannel__ne=0):
        if server.assistschannel in (0, "0", None):
            continue
        elif user.factionid not in server.assist_factions:
            continue
        elif server.sid not in [1132079436691415120]:
            continue

        try:
            messages.append(
                discordpost.delay(
                    f"channels/{server.assistschannel}/messages", payload=payload, channel=server.assistschannel
                )
            )
        except (DiscordError, NetworkingError):
            continue

        servers_forwarded.append(server)

    packed_messages = set()

    message: AsyncResult
    for message in messages:
        try:
            message: dict = message.get()
        except (DiscordError, NetworkingError):
            continue
        except Exception:
            continue

        packed_messages.add(f"{message['channel_id']}|{message['id']}")

    client.set(f"tornium:assists:{guid}:messages", packed_messages, nx=True, ex=600)

    return (
        jsonify(
            {
                "code": 1,
                "name": "OK",
                "message": "Server request was successful.",
                "servers_forwarded": len(servers_forwarded),
                "latency": round(time.time() - start_ts, 2),
            }
        ),
        200,
        api_ratelimit_response(key),
    )
