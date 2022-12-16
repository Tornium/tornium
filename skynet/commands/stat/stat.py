# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from mongoengine.queryset.visitor import Q

from models.faction import Faction
from models.statmodel import StatModel
from models.user import User
from models.usermodel import UserModel
import skynet.skyutils
import tasks
import utils


def stat(interaction):
    print(interaction)

    if "member" in interaction:
        user: UserModel = UserModel.objects(
            discord_id=interaction["member"]["user"]["id"]
        ).first()
    else:
        user: UserModel = UserModel.objects(
            discord_id=interaction["user"]["id"]
        ).first()

    tid = -1
    name = -1

    if "options" in interaction:
        tid = utils.find_list(interaction["data"]["options"], "name", "tornid")
        name = utils.find_list(interaction["data"]["options"], "name", "name")

        if (tid == -1 and name == -1) or (tid != -1 and name != -1):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Parameters",
                            "description": "The parameter passed must be either the Torn ID or a member mention.",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

    admin_keys = skynet.skyutils.get_admin_keys(interaction)

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
                            "color": 0xC83F49,
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
                            "color": 0xC83F49,
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
                            "color": 0xC83F49,
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
                        "color": 0xC83F49,
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
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if tid != -1:
        target: StatModel = (
            StatModel.objects(
                Q(tid=tid)
                & (
                    Q(globalstat=True)
                    | Q(addedid=user.tid)
                    | Q(addedfactiontid=user.factiontid)
                )
            )
            .order_by("-timeadded")
            .first()
        )
    elif name != -1:
        target_user: UserModel = UserModel.objects(name=name).first()

        if target_user is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Unknown User",
                            "description": "No Torn user could be located in the database with that name.",
                            "color": 0xC83F49,
                        }
                    ]
                },
            }

        target: StatModel = (
            StatModel.objects(
                Q(tid=target_user.tid)
                & (
                    Q(globalstat=True)
                    | Q(addedid=user.tid)
                    | Q(addedfactiontid=user.factiontid)
                )
            )
            .order_by("-timeadded")
            .first()
        )

    if target is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Not Located",
                        "description": "The specified user could not be found with your permissions in the stat database.",
                        "color": 0xC83F49,
                    }
                ]
            },
        }

    target_user: User = User(target.tid)
    target_user.refresh(key=random.choice(admin_keys))

    if target_user.factiontid != 0:
        target_faction = Faction(user.factiontid)
    else:
        target_faction = None

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": f"[{user.name} [{user.tid}]](https://www.torn.com/profiles.php?XID={user.tid})",
                    "fields": [
                        {
                            "name": "Faction",
                            "value": f"{target_faction.name if target_faction is not None else 'Unknown/No Faction'}",
                        },
                        {
                            "name": "Estimated Stat Score",
                            "value": utils.commas(round(target.battlescore, 2)),
                            "inline": True,
                        },
                        {
                            "name": "Stat Score Update",
                            "value": f"<t:{target.timeadded}:R>",
                            "inline": True,
                        },
                    ],
                }
            ]
        },
    }