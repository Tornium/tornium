# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import math
import random
import time

import mongoengine
from mongoengine.queryset.visitor import Q

from models.statmodel import StatModel
from models.user import User
from models.usermodel import UserModel
import skynet.skyutils
import tasks
import utils


def chain(interaction):
    print(interaction)

    start = time.time()

    if "member" in interaction:
        user: UserModel = UserModel.objects(
            discord_id=interaction["member"]["user"]["id"]
        ).first()
    else:
        user: UserModel = UserModel.objects(
            discord_id=interaction["user"]["id"]
        ).first()

    if "options" in interaction["data"]:
        length = utils.find_list(interaction["data"]["options"], "name", "length")
        ff = utils.find_list(interaction["data"]["options"], "name", "fairfight")
        variance = 0.01
    else:
        length = 10
        ff = 3
        variance = 0.01

    if type(length) != int:
        length = length[1]["value"]
    if type(ff) != int:
        ff = round(length[1]["value"], 2)

    if ff == 3:
        variance = 0

    admin_keys = skynet.skyutils.get_admin_keys(interaction)

    try:
        tasks.discordpost(
            f"interactions/{interaction['id']}/{interaction['token']}/callback",
            payload={
                "type": 5
            }
        )
    except utils.DiscordError as e:
        print(e)
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": f"Discord Error #{e.code}",
                        "description": f"{e.message}",
                        "color": skynet.skyutils.SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    except Exception as e:
        print(e)
        return {}

    if user is None:
        try:
            user_data = tasks.tornget(
                f"user/{interaction['member']['user']['id']}?selections=profile,discord",
                random.choice(admin_keys),
            )
        except utils.TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Torn API Error",
                            "description": f'The Torn API has raised error code {e.code}: "{e.message}".',
                            "color": skynet.skyutils.SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
        except utils.NetworkingError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "HTTP Error",
                            "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
                            "color": skynet.skyutils.SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        user: UserModel = UserModel.objects(tid=user_data["player_id"]).modify(
            upsert=True,
            new=True,
            set__name=user_data["name"],
            set__level=user_data["level"],
            set__last_refresh=utils.now(),
            set__discord_id=user_data["discord"]["discordID"]
            if user_data["discord"]["discordID"] != ""
            else 0,
            set__factionid=user_data["faction"]["faction_id"],
            set__status=user_data["last_action"]["status"],
            set__last_action=user_data["last_action"]["timestamp"],
        )

        if user.discord_id == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "User Requires Verification",
                            "description": "You are required to be verified officially by Torn through the "
                            "[official Torn Discord server](https://www.torn.com/discord] before being "
                            "able to utilize the banking features of this bot. Alternatively, you can "
                            "sign into [the web dashboard](https://tornium.com/faction/banking) with "
                            "your API key to send a request without verifying. If you have recently "
                            "verified yourself, please wait a minute or two before trying again.",
                            "color": skynet.skyutils.SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
    elif user.tid == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Requires Verification",
                        "description": "You are required to be verified officially by Torn through the "
                        "[official Torn Discord server](https://www.torn.com/discord] before being "
                        "able to utilize the banking features of this bot. Alternatively, you can "
                        "sign into [the web dashboard](https://tornium.com/faction/banking) with "
                        "your API key to send a request without verifying. If you have recently "
                        "verified yourself, please wait a minute or two before trying again.",
                        "color": skynet.skyutils.SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    try:
        user: User = User(user.tid)
        user.refresh(key=random.choice(admin_keys), force=True)
    except utils.MissingKeyError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Key Available",
                        "description": "No Torn API key could be utilized for this request.",
                        "color": skynet.skyutils.SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if user.battlescore == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Stats Missing",
                        "description": "The user's battle stats could not be located in the database. Please sign into "
                                       "Tornium.",
                        "color": skynet.skyutils.SKYNET_ERROR
                    }
                ],
                "flags": 64,  # Ephemeral
            }
        }

    # f = fair fight
    # v = variance
    # d = defender's stat score
    # a = attacker's stat score
    #
    # f +- v = 1 + 8/3 * d/a
    # 0.375 * a * (f +- v - 1) = d

    stat_entries: mongoengine.QuerySet = StatModel.objects(
        (
            Q(globalstat=True)
            | Q(addedid=user.tid)
            | Q(addedfactiontid=user.factiontid)
        )
        & Q(
            battlescore__gte=(
                0.375 * user.battlescore * (ff - variance - 1)
            )
        )
        & Q(
            battlescore__lte=(
                0.375 * user.battlescore * (ff + variance - 1)
            )
        )
    )

    if stat_entries.count():
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No Targets Located",
                        "description": "No chain targets could be located with the following settings.",
                        "color": skynet.skyutils.SKYNET_ERROR,
                        "fields": [
                            {
                                "name": "Length",
                                "value": length,
                                "inline": True,
                            },
                            {
                                "name": "Fair Fight",
                                "value": ff,
                                "inline": True,
                            },
                            {
                                "Name": "Variance",
                                "value": variance,
                                "inline": True,
                            }
                        ]
                    }
                ]
            }
        }

    stat_entries: list = list(set(stat_entries.all().values_list("tid")))
    random.shuffle(stat_entries)
    jsonified_stat_entires = []

    targets = {}
    targets_updated = 0

    for stat_entry in stat_entries:
        stat: StatModel = (
            StatModel.objects(
                Q(tid=stat_entry)
                & (
                    Q(globalstat=True)
                    | Q(addedid=user.tid)
                    | Q(addedfactiontid=user.factiontid)
                )
            )
            .order_by("-timeadded")
            .first()
        )

        if stat_entry in targets:
            target = targets[stat_entry]
        else:
            target = User(tid=stat.tid)

            if targets_updated <= 50:
                if target.refresh(key=random.choice(admin_keys)):
                    targets_updated += 1

        target_ff = 1 + 8 / 3 * (stat.battlescore / user.battlescore)

        jsonified_stat_entires.append(
            {
                "statid": stat.statid,
                "tid": stat.tid,
                "battlescore": stat.battlescore,
                "timeadded": stat.timeadded,
                "ff": target_ff,
                "respect": round((math.log(target.level, 2) + 1) / 4, 2),
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

    embed = {
        "title": f"Chain List for {user.name} [{user.tid}]",
        "fields": [],
        "color": skynet.skyutils.SKYNET_GOOD,
        "footer": {
            "text": ""
        }
    }

    jsonified_stat_entires = sorted(jsonified_stat_entires, key=lambda d: d["respect"], reverse=True)
    stat_count = 0

    for stat_entry in jsonified_stat_entires:
        if stat_count >= length:
            break

        embed["fields"].append({
            "name": f"{stat_entry['user']['name']} [{stat_entry['user']['tid']}]",
            "value": f"Stat Score: {utils.commas(stat_entry['battlescore'])}\nRespect: {stat_entry['respect']}",
            "inline": True,
        })

        stat_count += 1

    embed["description"] = f"Showing {stat_count} of {len(jsonified_stat_entires)} chain targets..."
    embed["footer"] = {
        "text": f"Run time: {round(time.time() - start, 2)} seconds"
    }

    tasks.discordpatch(
        f"webhooks/{interaction['application_id']}/{interaction['token']}/messages/@original",
        payload={
            "type": 4,
            "data": {
                "embeds": [embed]
            }
        }
    )
