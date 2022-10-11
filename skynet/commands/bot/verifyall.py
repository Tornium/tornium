# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

import jinja2

from models.factionmodel import FactionModel
from models.server import Server
from models.user import User
from models.usermodel import UserModel
from skynet.skyutils import get_admin_keys
import tasks
import utils


def verifyall(interaction):
    print(interaction)

    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Location",
                        "description": "The verification command must be run in a server where verification is setup "
                        "and enabled.",
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    server = Server(interaction["guild_id"])

    if server.config.get("verify") in (None, 0):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Verification Not Enabled",
                        "description": "Verification is not enabled in the server's admin dashboard.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif (
        server.verify_template == ""
        and len(server.verified_roles) == 0
        and len(server.faction_verify) == 0
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Verification Not Enabled",
                        "description": "Verification is enabled, but nothing will be changed based on the current "
                        "settings in the server's admin dashboard.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if "member" in interaction:
        user: UserModel = UserModel.objects(
            discord_id=interaction["member"]["user"]["id"]
        ).first()
    else:
        user: UserModel = UserModel.objects(
            discord_id=interaction["user"]["id"]
        ).first()

    if "options" in interaction["data"]:
        force = utils.find_list(interaction["data"]["option"], "name", "force")
    else:
        force = -1

    try:
        server_data = tasks.discordget(f"guilds/{server.sid}?with_counts=true")
        print(server_data)
    except utils.DiscordError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Discord API Error",
                        "description": f'The Discord API has raised error code {e.code}: "{e.message}".',
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
                        "description": f'The Discord API has returned an HTTP error {e.code}: "{e.message}".',
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    member_count = 0
    member_fetch_run = 0

    while (
        member_count >= server_data["approximate_member_count"] * 0.99
        and member_fetch_run < (server_data["approximate_member_count"] // 1000 + 1)
        and member_fetch_run < 100
    ):
        try:
            guild_members = tasks.discordget(
                f"guilds/{server.sid}/members?limit=1000", dev=server.skynet
            )
            print(guild_members)
        except utils.DiscordError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Discord API Error",
                            "description": f'The Discord API has raised error code {e.code}: "{e.message}".',
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
                            "description": f'The Discord API has returned an HTTP error {e.code}: "{e.message}".',
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        member_count += len(guild_members)
        member_fetch_run += 1

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Verification Complete",
                    "description": f"Approximately {server_data['approximate_member_count']}; Accurately {member_count}",
                }
            ]
        },
    }
