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
from peewee import DoesNotExist
from tornium_celery.tasks.api import discordget, discordpatch
from tornium_celery.tasks.user import update_user
from tornium_commons.errors import TornError
from tornium_commons.formatters import find_list
from tornium_commons.models import Faction, Server, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO

from skynet.skyutils import get_admin_keys


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
                "flags": 64,
            },
        }

    try:
        guild: Server = Server.get_by_id(interaction["guild_id"])
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Not Located",
                        "description": "This server could not be located in Tornium's database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    if not guild.verify_enabled:
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
                "flags": 64,
            },
        }
    elif guild.verify_template == "" and len(guild.verified_roles) == 0 and len(guild.faction_verify) == 0:
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
                "flags": 64,
            },
        }

    user: User = kwargs["invoker"]

    if "options" in interaction["data"]:
        member = find_list(interaction["data"]["options"], "name", "member")
        force = find_list(interaction["data"]["options"], "name", "force")
    else:
        member = None
        force = None

    admin_keys = kwargs.get("admin_keys", get_admin_keys(interaction))

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
                "flags": 64,
            },
        }

    update_user_kwargs = {
        "key": random.choice(admin_keys),
        "refresh_existing": True,
    }

    if member is not None:
        update_user_kwargs["discordid"] = int(member["value"])
    else:
        update_user_kwargs["discordid"] = user.discord_id

    if member is not None:
        discord_member = discordget(f"guilds/{guild.sid}/members/{update_user_kwargs['discordid']}")
        user_roles = discord_member["roles"]

        if discord_member.get("nick") in (None, ""):
            current_nick = discord_member["user"]["username"]
        else:
            current_nick = discord_member["nick"]
    else:
        user_roles = interaction["member"]["roles"]

        if interaction["member"].get("nick") in (None, ""):
            current_nick = interaction["member"]["user"]["username"]
        else:
            current_nick = interaction["member"]["nick"]

    if set(user_roles) & set(map(str, guild.exclusion_roles)):  # Exclusion role in member's roles
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Verification Failed",
                        "description": "The user has an exclusion role which prevents automatic verification. "
                        "Contact a server admin to remove this exclusion role or to manually set roles.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        update_user(**update_user_kwargs)  # TODO: Handle Torn and Network errors
    except TornError as e:
        if e.code == 6:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Verification Failed",
                            "description": "API call failed. Please verify that you are officially verified by Torn. "
                            "Otherwise, try forcing the verification. To verify on Torn, you can match your Discord and "
                            "Torn accounts through the [official Torn Discord server](https://www.torn.com/discord) or "
                            "through a [direct OAuth link](https://discordapp.com/api/oauth2/authorize?client_id=441210177971159041&redirect_uri=https%3A%2F%2Fwww.torn.com%2Fdiscord.php&response_type=code&scope=identify).",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        raise e

    try:
        user: User = User.get(User.discord_id == update_user_kwargs["discordid"])
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Not Found",
                        "description": "The user could not be found in the database after a refresh.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
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
                        "Otherwise, try forcing the verification. To verify on Torn, you can match your Discord and "
                        "Torn accounts through the [official Torn Discord server](https://www.torn.com/discord) or "
                        "through a [direct OAuth link](https://discordapp.com/api/oauth2/authorize?client_id=441210177971159041&redirect_uri=https%3A%2F%2Fwww.torn.com%2Fdiscord.php&response_type=code&scope=identify).",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    patch_json = {}
    faction: Faction = user.faction

    if guild.verify_template != "":
        nick = (
            jinja2.Environment(autoescape=True)
            .from_string(guild.verify_template)
            .render(name=user.name, tid=user.tid, tag="" if faction is None else faction.tag)
        )

        if nick != current_nick:
            patch_json["nick"] = nick

    if len(guild.verified_roles) != 0 and user.discord_id != 0:
        verified_role: int
        for verified_role in guild.verified_roles:
            if str(verified_role) in user_roles:
                continue
            elif patch_json.get("roles") is None:
                patch_json["roles"] = user_roles

            patch_json["roles"].append(str(verified_role))

    if (
        user.faction is not None
        and guild.faction_verify.get(str(user.faction_id)) is not None
        and guild.faction_verify[str(user.faction_id)].get("roles") is not None
        and len(guild.faction_verify[str(user.faction_id)]["roles"]) != 0
        and guild.faction_verify[str(user.faction_id)].get("enabled") not in (None, False)
    ):
        faction_role: int
        for faction_role in guild.faction_verify[str(user.faction_id)]["roles"]:
            if str(faction_role) in user_roles:
                continue
            elif patch_json.get("roles") is None:
                patch_json["roles"] = user_roles

            patch_json["roles"].append(str(faction_role))

    for factiontid, faction_verify_data in guild.faction_verify.items():
        for faction_role in faction_verify_data["roles"]:
            if str(faction_role) in user_roles and int(factiontid) != user.faction_id:
                if guild.faction_verify.get(str(user.faction_id)) is not None and faction_role in guild.faction_verify[
                    str(user.faction_id)
                ].get("roles", []):
                    continue
                elif patch_json.get("roles") is None:
                    patch_json["roles"] = user_roles

                patch_json["roles"].remove(str(faction_role))

    if (
        user.faction is not None
        and user.faction_position is not None
        and guild.faction_verify.get(str(user.faction_id)) is not None
        and guild.faction_verify[str(user.faction_id)].get("positions") is not None
        and len(guild.faction_verify[str(user.faction_id)]["positions"]) != 0
        and str(user.faction_position) in guild.faction_verify[str(user.faction_id)]["positions"].keys()
        and guild.faction_verify[str(user.faction_id)].get("enabled") not in (None, False)
    ):
        position_role: int
        for position_role in guild.faction_verify[str(user.faction_id)]["positions"][str(user.faction_position)]:
            if str(position_role) in user_roles:
                continue
            elif patch_json.get("roles") is None:
                patch_json["roles"] = user_roles

            patch_json["roles"].append(str(position_role))

    valid_position_roles = []

    for factiontid, faction_positions_data in guild.faction_verify.items():
        if "positions" not in faction_positions_data:
            continue

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
                    elif patch_json.get("roles") is None:
                        patch_json["roles"] = user_roles

                    patch_json["roles"].remove(str(position_role))

    if len(patch_json) == 0 and (force is None or (type(force) == list and not force.get("value"))):
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
                "flags": 64,
            },
        }

    if "roles" in patch_json:
        patch_json["roles"] = list(set(patch_json["roles"]))

    discordpatch(
        f"guilds/{guild.sid}/members/{user.discord_id}",
        patch_json,
    )

    if user.faction is None:
        faction_str = "None"
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
