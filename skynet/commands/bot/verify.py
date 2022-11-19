# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

import jinja2
from mongoengine.queryset.visitor import Q

from models.factionmodel import FactionModel
from models.positionmodel import PositionModel
from models.server import Server
from models.user import User
from models.usermodel import UserModel
from skynet.skyutils import get_admin_keys
import tasks
import utils


def verify(interaction):
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

        discord_id = interaction["member"]["user"]["id"]
        user_roles = interaction["member"]["roles"]
    else:
        user: UserModel = UserModel.objects(
            discord_id=interaction["user"]["id"]
        ).first()

        discord_id = interaction["member"]["user"]["id"]
        user_roles = interaction["user"]["roles"]

    if "options" in interaction["data"]:
        member = utils.find_list(interaction["data"]["options"], "name", "member")
        force = utils.find_list(interaction["data"]["options"], "name", "force")
    else:
        member = -1
        force = -1

    if member != -1:
        user: UserModel = UserModel.objects(discord_id=member[1]["value"]).first()

        discord_id = member[1]["value"]

        try:
            discord_member = tasks.discordget(
                f"guilds/{server.sid}/members/{discord_id}", dev=server.skynet
            )
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
                            "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        user_roles = discord_member["roles"]

    admin_keys = get_admin_keys(interaction)

    if len(admin_keys) == 0:
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
            },
        }

    if user is None:
        try:
            user_data = tasks.tornget(
                f"user/{discord_id}?selections=profile,discord",
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
                            "sign into [the web dashboard](https://torn.deek.sh/faction/banking) with "
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
                        "sign into [the web dashboard](https://torn.deek.sh/faction/banking) with "
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
        user.refresh(
            key=random.choice(admin_keys), force=True if force != -1 else False
        )
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

    if user.discord_id in (0, None):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Verification Failed",
                        "description": "No Discord ID found. Please verify that you are officially verified by Torn. "
                        "Otherwise, try forcing the verification.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    patch_json = {}

    if server.verify_template != "":
        nick = (
            jinja2.Environment()
            .from_string(server.verify_template)
            .render(name=user.name, tid=user.tid, tag="")
        )

        if nick != interaction["member"]["nick"]:
            patch_json["nick"] = nick

    if len(server.verified_roles) != 0 and user.discord_id != 0:
        verified_role: int
        for verified_role in server.verified_roles:
            if str(verified_role) in user_roles:
                continue
            elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                patch_json["roles"] = user_roles

            patch_json["roles"].append(str(verified_role))
    elif user.discord_id == 0 and len(server.verified_roles) != 0:
        verified_role: int
        for verified_role in server.verified_roles:
            if str(verified_role) in user_roles:
                if patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                    patch_json["roles"] = user_roles

                patch_json["roles"].remove(str(verified_role))

    if (
        user.factiontid != 0
        and server.faction_verify.get(str(user.factiontid)) is not None
        and server.faction_verify[str(user.factiontid)].get("roles") is not None
        and len(server.faction_verify[str(user.factiontid)]["roles"]) != 0
        and server.faction_verify[str(user.factiontid)].get("enabled")
        not in (None, False)
    ):
        faction_role: int
        for faction_role in server.faction_verify[str(user.factiontid)]["roles"]:
            if str(faction_role) in user_roles:
                continue
            elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                patch_json["roles"] = user_roles

            patch_json["roles"].append(str(faction_role))

    for factiontid, faction_verify_data in server.faction_verify.items():
        for faction_role in faction_verify_data["roles"]:
            if str(faction_role) in user_roles and int(factiontid) != user.factiontid:
                if patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                    patch_json["roles"] = user_roles

                patch_json["roles"].remove(str(faction_role))

    if (
            user.factiontid != 0
            and user.faction_position is not None
            and server.faction_verify.get(str(user.factiontid)) is not None
            and server.faction_verify[str(user.factiontid)].get("positions") is not None
            and len(server.faction_verify[str(user.factiontid)]["positions"]) != 0
            and str(user.faction_position) in server.faction_verify[str(user.factiontid)]["positions"].keys()
            and server.faction_verify[str(user.factiontid)].get("enabled") not in (None, False)
    ):
        position_role: int
        for position_role in server.faction_verify[str(user.factiontid)]["positions"][str(user.faction_position)]:
            if str(position_role) in user_roles:
                continue
            elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                patch_json["roles"] = user_roles

            patch_json["roles"].append(str(position_role))

    for factiontid, faction_positions_data in server.faction_verify.items():
        for position_uuid, position_data in faction_positions_data["positions"].items():
            if position_uuid == str(user.faction_position):
                continue

            for position_role in position_data:
                if position_role in user_roles:
                    print(str(user.faction_position) in faction_positions_data["positions"])
                    print(position_role in faction_positions_data["positions"][str(user.faction_position)])

                    print(f"{position_role}: {type(position_role)}")
                    print(faction_positions_data["positions"][str(user.faction_position)])

                    if str(user.faction_position) in faction_positions_data["positions"] and position_role in faction_positions_data["positions"][str(user.faction_position)]:
                        continue
                    elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                        patch_json["roles"] = user_roles

                    patch_json["roles"].remove(str(position_role))

    if len(patch_json) == 0 and (
        force == -1 or (type(force) == list and not force[1].get("value"))
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Verification Already Completed",
                        "description": "The verification would have modified no values. Run the command with force if "
                        "you believe something has changed.",
                        "color": 0x7DF9FF,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if "roles" in patch_json:
        patch_json["roles"] = list(set(patch_json["roles"]))

    try:
        response = tasks.discordpatch(
            f"guilds/{server.sid}/members/{user.discord_id}",
            patch_json,
            dev=server.skynet,
        )
        print(response)
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
                        "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    faction: FactionModel = (
        FactionModel.objects(tid=user.factiontid).first()
        if user.factiontid != 0
        else None
    )

    if user.factiontid == 0:
        faction_str = "None"
    elif user.factiontid is None:
        faction_str = "Unknown Faction"
    else:
        faction_str = f"{faction.name} [{faction.tid}]"

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Verification Successful",
                    "description": f"""User: [{user.name} [{user.tid}]](https://www.torn.com/profiles.php?XID={user.tid})
                    Faction: {faction_str}
                    Discord: <@{user.discord_id}>""",
                    "color": 0x32CD32,
                }
            ]
        },
    }
