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

import inspect
import random

import jinja2

import tasks
import tasks.user
import utils
from models.factionmodel import FactionModel
from models.server import Server
from models.usermodel import UserModel
from skynet.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO, get_admin_keys, invoker_exists


@invoker_exists
def verify(interaction, *args, **kwargs):
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
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif server.verify_template == "" and len(server.verified_roles) == 0 and len(server.faction_verify) == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Verification Not Enabled",
                        "description": "Verification is enabled, but nothing will be changed based on the current "
                        "settings in the server's admin dashboard.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    user: UserModel = kwargs["invoker"]

    if "options" in interaction["data"]:
        member = utils.find_list(interaction["data"]["options"], "name", "member")
        force = utils.find_list(interaction["data"]["options"], "name", "force")
    else:
        member = -1
        force = -1

    admin_keys = kwargs.get("admin_keys")

    if admin_keys is None:
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
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    update_user_kwargs = {
        "key": random.choice(admin_keys),
        "refresh_existing": True,
    }

    if member != -1:
        update_user_kwargs["discordid"] = member[1]["value"]
    else:
        update_user_kwargs["discordid"] = user.discord_id

    try:
        user: UserModel = tasks.user.update_user(**update_user_kwargs)
    except utils.MissingKeyError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Key Available",
                        "description": "No Torn API key could be utilized for this request.",
                        "color": SKYNET_ERROR,
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
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if member != -1:
        try:
            discord_member = tasks.discordget(f"guilds/{server.sid}/members/{user.discord_id}")
        except utils.DiscordError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Discord API Error",
                            "description": f'The Discord API has raised error code {e.code}: "{e.message}".',
                            "color": SKYNET_ERROR,
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
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        user_roles = discord_member["roles"]
    else:
        user_roles = interaction["member"]["roles"]

    patch_json = {}

    if server.verify_template != "":
        nick = (
            jinja2.Environment(autoescape=True)
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
        user.factionid != 0
        and server.faction_verify.get(str(user.factionid)) is not None
        and server.faction_verify[str(user.factionid)].get("roles") is not None
        and len(server.faction_verify[str(user.factionid)]["roles"]) != 0
        and server.faction_verify[str(user.factionid)].get("enabled") not in (None, False)
    ):
        faction_role: int
        for faction_role in server.faction_verify[str(user.factionid)]["roles"]:
            if str(faction_role) in user_roles:
                continue
            elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                patch_json["roles"] = user_roles

            patch_json["roles"].append(str(faction_role))

    for factiontid, faction_verify_data in server.faction_verify.items():
        for faction_role in faction_verify_data["roles"]:
            if str(faction_role) in user_roles and int(factiontid) != user.factionid:
                if patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                    patch_json["roles"] = user_roles

                patch_json["roles"].remove(str(faction_role))

    if (
        user.factionid != 0
        and user.faction_position is not None
        and server.faction_verify.get(str(user.factionid)) is not None
        and server.faction_verify[str(user.factionid)].get("positions") is not None
        and len(server.faction_verify[str(user.factionid)]["positions"]) != 0
        and str(user.faction_position) in server.faction_verify[str(user.factionid)]["positions"].keys()
        and server.faction_verify[str(user.factionid)].get("enabled") not in (None, False)
    ):
        position_role: int
        for position_role in server.faction_verify[str(user.factionid)]["positions"][str(user.faction_position)]:
            if str(position_role) in user_roles:
                continue
            elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                patch_json["roles"] = user_roles

            patch_json["roles"].append(str(position_role))

    valid_position_roles = []

    for factiontid, faction_positions_data in server.faction_verify.items():
        for position_uuid, position_data in faction_positions_data["positions"].items():
            for position_role in position_data:
                if position_role in valid_position_roles:
                    continue
                elif position_role in user_roles:
                    if (
                        str(user.faction_position) in faction_positions_data["positions"]
                        and position_role in faction_positions_data["positions"][str(user.faction_position)]
                    ):
                        valid_position_roles.append(position_role)
                        continue
                    elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
                        patch_json["roles"] = user_roles

                    patch_json["roles"].remove(str(position_role))

    if len(patch_json) == 0 and (force == -1 or (type(force) == list and not force[1].get("value"))):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Verification Already Completed",
                        "description": "The verification would have modified no values. Run the command with force if "
                        "you believe something has changed.",
                        "color": SKYNET_INFO,
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

    faction: FactionModel = FactionModel.objects(tid=user.factionid).first() if user.factionid != 0 else None

    if user.factionid == 0:
        faction_str = "None"
    elif user.factionid is None:
        faction_str = "Unknown Faction"
    else:
        faction_str = f"{faction.name} [{faction.tid}]"

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Verification Successful",
                    "description": inspect.cleandoc(
                        f"""User: [{user.name} [{user.tid}]](https://www.torn.com/profiles.php?XID={user.tid})
                        Faction: {faction_str}
                        Discord: <@{user.discord_id}>"""
                    ),
                    "color": SKYNET_GOOD,
                }
            ]
        },
    }
