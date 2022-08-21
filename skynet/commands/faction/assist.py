# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import random
import time
from urllib.parse import urlparse, parse_qs

from models.factionmodel import FactionModel
from models.server import Server
from models.servermodel import ServerModel
from models.user import User
from models.usermodel import UserModel
import redisdb
from skynet.skyutils import get_admin_keys
import tasks
import utils


def assist(interaction):
    print(interaction)

    start_time = time.time()

    if "member" in interaction:
        user: UserModel = UserModel.objects(
            discord_id=interaction["member"]["user"]["id"]
        ).first()
    else:
        user: UserModel = UserModel.objects(
            discord_id=interaction["user"]["id"]
        ).first()

    if "options" not in interaction["data"]:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Assist Request Failed",
                        "description": "No options were passed with the command.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    tid = utils.find_list(interaction["data"]["options"], "name", "tornid")
    url = utils.find_list(interaction["data"]["options"], "name", "url")

    if (tid == -1 and url == -1) or (tid != -1 and url != -1):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameters",
                        "description": "The parameter passed must be either the Torn ID or the URL.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif tid != -1:
        target: User = User(tid[1]["value"])
    elif url != -1:
        # https://www.torn.com/loader.php?sid=attack&user2ID=1009878
        parsed_url = urlparse(url[1]["value"])

        if (
            parsed_url.hostname == "www.torn.com"
            and parsed_url.path in ("/loader.php", "/loader2.php")
            and parse_qs(parsed_url.query)["sid"][0] in ("attack", "getInAttack")
        ):
            target: User = User(parse_qs(parsed_url.query)["user2ID"][0])
        else:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Attack URL",
                            "description": "The passed attack URL was not valid.",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Unknown Parameter",
                        "description": "Confusion!",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if user.key != "" or "guild_id" in interaction:
        keys = get_admin_keys(interaction)

        if len(keys) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No API Keys",
                            "description": "No API keys were found to be run for this command. Please sign into "
                                           "Tornium or run this command in a server with signed-in admins.",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }

        target.refresh(key=random.choice(get_admin_keys(interaction)))
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Error",
                        "description": "Unable to refresh target's data. Please sign into Tornium or run this in a server.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if redisdb.get_redis().get(f"tornium:assist-ratelimit:{user.tid}") is not None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Ratelimit Reached",
                        "description": "You have reached the ratelimit for assist requests (once every thirty seconds).",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    else:
        redisdb.get_redis().set(f"tornium:assist-ratelimit:{user.tid}", 1)
        redisdb.get_redis().expire(f"tornium:assist-ratelimit:{user.tid}", 30)

    if target.tid == user.tid:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Same User",
                        "description": "The user requested for the assist is the same as the requester.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    target_faction: FactionModel = FactionModel.objects(tid=target.factiontid).first()

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
                            "value": f"{FactionModel.objects(tid=user.factionid).first().name} [{user.factionid}]",
                            "inline": True,
                        },
                    ],
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "footer": {
                        "text": f"Latency: {round(time.time() - start_time, 2)} seconds"
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

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Assist Request Forwarded",
                    "description": f"The assist request on [{target.name} [{target.tid}]](https://www.torn.com/profiles.php?XID={target.tid})",
                    "footer": {"text": f"Servers Forwarded: {len(servers_forwarded)}"},
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }
