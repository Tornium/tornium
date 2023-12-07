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
from peewee import DoesNotExist
from redis.commands.json.path import Path
from tornium_celery.tasks.api import discordpost
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.formatters import bs_to_range, commas
from tornium_commons.models import Faction, PersonalStats, Server, Stat, User

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

    try:
        user: User = User.get_by_id(user_tid)
    except DoesNotExist:
        return make_exception_response("1100", redis_client=client)

    key = f"tornium:ratelimit:{user_tid}"
    assist_lock_key = f"tornium:assists:{target_tid}:lock"

    if client.exists(assist_lock_key):
        return make_exception_response("4291", key, redis_client=client)
    else:
        client.set(
            assist_lock_key,
            int(datetime.datetime.utcnow().timestamp()) + 10,
            nx=True,
            ex=10,
        )

    if user.faction is None:
        return make_exception_response("1102", key, redis_client=client)

    call_key: str
    if user.key in ("", None):
        if len(user.faction.aa_keys) == 0:
            return make_exception_response("1200", redis_client=client)

        call_key = random.choice(user.faction.aa_keys)
    else:
        call_key = user.key

    try:
        update_user(key=call_key, tid=target_tid, refresh_existing=False)
    except AttributeError:
        pass

    try:
        target: User = User.select().where(User.tid == target_tid).first()
    except DoesNotExist:
        return make_exception_response("1100", key, redis_client=client)

    if target.faction is not None:
        if target.faction.tag in ("", None):
            content_target_faction = target.faction.name
        else:
            content_target_faction = target.faction.tag
    else:
        content_target_faction = ""

    if user.faction is not None:
        if user.faction.tag in ("", None):
            user_faction_str = user.faction.name
        else:
            user_faction_str = user.faction.tag
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
                "url": f"https://tornium.com/faction/assists/{guid}?mode=heavy",
            }
        )
        fields_payload.append(
            {
                "name": "Heavies Needed",
                "value": heavies,
                "inline": True,
            }
        )

    if tears > 0:
        requested_types.append(f"{tears}x tears")
        components_payload.append(
            {
                "type": 2,
                "style": 5,
                "label": "Join Tears",
                "url": f"https://tornium.com/faction/assists/{guid}?mode=tear",
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
                "url": f"https://tornium.com/faction/assists/{guid}?mode=smoke",
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
    client.set(
        f"tornium:assists:{guid}",
        f"{target_tid}|{user_tid}|{smokes}|{tears}|{heavies}",
        nx=True,
        ex=600,
    )

    payload = {
        "content": f"Assist on {target.name} [{content_target_faction}]",
        "embeds": [
            {
                "title": f"{user.name} [{user_faction_str}] needs help with {target.name} [{content_target_faction}]",
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

    stat: typing.Optional[Stat] = Stat.select(Stat.battlescore, Stat.time_added).where(
        (Stat.tid == target_tid)
        & (
            (Stat.added_group == 0)
            | (Stat.added_group == user.faction_id)
        )
    ).order_by(-Stat.time_added).first()

    total_bs = None

    if stat is not None:
        total_bs = int(sum(bs_to_range(stat.battlescore)) / 2)

        payload["embeds"][1]["fields"].append(
            {
                "name": "Estimated Total Stats",
                "value": commas(total_bs),
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

    ps: typing.Optional[PersonalStats]
    try:
        ps = PersonalStats.select().where(PersonalStats.tid == target_tid).order_by(-PersonalStats.timestamp).get()
    except DoesNotExist:
        ps = None

    if ps is not None:
        payload["embeds"][1]["description"] = inspect.cleandoc(
            f"""Xanax Used: {commas(ps.xantaken)}
            Refills Used: {commas(ps.refills)}
            Energy Drinks Drunk: {commas(ps.energydrinkused)}
            LSD Used: {commas(ps.lsdtaken)}
            SEs Used: {commas(ps.statenhancersused)}
            
            ELO: {commas(ps.elo)}
            Best Damage: {commas(ps.bestdamage)}
            Networth: ${commas(ps.networth)}
            
            Personal Stat Last Update: <t:{int(ps.timestamp.timestamp())}:R>
            """  # noqa: W293
        )

    client.json().set(f"tornium:assists:{guid}:payload", Path.root_path(), payload, nx=True)
    client.expire(f"tornium:assists:{guid}:payload", 600)

    l0_roles_enabled = False  # 500m+
    l1_roles_enabled = False  # 1b+
    l2_roles_enabled = False  # 2b+
    l3_roles_enabled = False  # 5b+

    if total_bs is not None:
        distraction = smokes + tears + heavies
        distracted_eff_bs = total_bs / pow(2, distraction)

        if distracted_eff_bs <= 750_000_000:
            l0_roles_enabled = True
        elif distracted_eff_bs <= 1_000_000_000:
            l0_roles_enabled = True
            l1_roles_enabled = True
        elif distracted_eff_bs <= 1_500_00_000:
            l1_roles_enabled = True
        elif distracted_eff_bs <= 2_000_000_000:
            l1_roles_enabled = True
            l2_roles_enabled = True
        elif distracted_eff_bs <= 3_500_000_000:
            l2_roles_enabled = True
        elif distracted_eff_bs <= 5_000_000_000:
            l2_roles_enabled = True
            l3_roles_enabled = True
        else:
            l3_roles_enabled = True

    servers_forwarded = []
    messages = []

    server: Server
    for server in Server.select().where(Server.assist_channel != 0):
        if server.assist_channel in (0, "0", None):
            continue
        elif user.faction.tid not in server.assist_factions:
            continue

        roles = []

        if smokes > 0 and len(server.assist_smoker_roles) != 0:
            roles.extend(list(server.assist_smoker_roles))

        if tears > 0 and len(server.assist_tear_roles) != 0:
            roles.extend(list(server.assist_tear_roles))

        if heavies > 0:
            heavies_roles = []

            if l0_roles_enabled and len(server.assist_l0_roles) != 0:
                heavies_roles.extend(list(server.assist_l0_roles))
            if l1_roles_enabled and len(server.assist_l1_roles) != 0:
                heavies_roles.extend(list(server.assist_l1_roles))
            if l2_roles_enabled and len(server.assist_l2_roles) != 0:
                heavies_roles.extend(list(server.assist_l2_roles))
            if l3_roles_enabled and len(server.assist_l3_roles) != 0:
                heavies_roles.extend(list(server.assist_l3_roles))

            if len(heavies_roles) == 0 and len(server.assist_l0_roles) != 0:
                heavies_roles = list(server.assist_l0_roles)

            roles.extend(heavies_roles)

        roles = list(set(roles))

        if len(roles) > 0:
            payload["content"] += "\n"

            for role in roles:
                payload["content"] += f"<@&{role}>"

        try:
            messages.append(
                discordpost.delay(
                    f"channels/{server.assist_channel}/messages",
                    payload=payload,
                    channel=server.assist_channel,
                )
            )
        except (DiscordError, NetworkingError):
            continue

        payload["content"] = payload["content"].split("\n")[0]
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

    client.json().set(
        f"tornium:assists:{guid}:messages",
        Path.root_path(),
        list(packed_messages),
        nx=True,
    )
    client.expire(f"tornium:assists:{guid}:messages", 600)

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
