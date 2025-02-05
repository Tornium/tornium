# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import inspect
import random
import typing

from peewee import DoesNotExist
from tornium_celery.tasks.api import discordget, discordpatch
from tornium_celery.tasks.guild import (
    invalid_member_faction_roles,
    invalid_member_position_roles,
    member_faction_roles,
    member_position_roles,
    member_verification_name,
    member_verified_roles,
)
from tornium_celery.tasks.user import update_user
from tornium_commons.errors import DiscordError, TornError
from tornium_commons.formatters import discord_escaper, find_list
from tornium_commons.models import Server, User
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

    user: typing.Optional[User] = kwargs["invoker"]

    if "options" in interaction["data"]:
        member = find_list(interaction["data"]["options"], "name", "member")
        force = find_list(interaction["data"]["options"], "name", "force")
    else:
        member = None
        force = None

    admin_keys = kwargs.get("admin_keys", get_admin_keys(interaction, all_keys=True))

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
    elif user is None:
        # This command can only be run in servers so this does not need to check for `interaction["user"]["id"]`
        update_user_kwargs["discordid"] = interaction["member"]["user"]["id"]
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
        update_user(**update_user_kwargs)
    except TornError as e:
        if e.code == 6:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Verification Failed",
                            "description": "This user may not be verified on Torn. Please make sure that the user is officially verified by Torn. "
                            "To verify on Torn, the user can link their Discord and Torn accounts through the "
                            "[official Torn Discord server](https://www.torn.com/discord) or through a "
                            "[direct OAuth link](https://discordapp.com/api/oauth2/authorize?client_id=441210177971159041&redirect_uri=https%3A%2F%2Fwww.torn.com%2Fdiscord.php&response_type=code&scope=identify). "
                            "Once the user is verified, user `/verify force:true` to verify the user.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        raise e

    try:
        # TODO: Limit selected fields
        user: User = User.select().where(User.discord_id == update_user_kwargs["discordid"]).get()
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
                        "description": "No Discord ID found. Please verify that the user is officially verified by Torn. "
                        "Otherwise, try forcing the verification. To verify on Torn, the user can link their Discord and "
                        "Torn accounts through the [official Torn Discord server](https://www.torn.com/discord) or "
                        "through a [direct OAuth link](https://discordapp.com/api/oauth2/authorize?client_id=441210177971159041&redirect_uri=https%3A%2F%2Fwww.torn.com%2Fdiscord.php&response_type=code&scope=identify).",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    patch_json = {
        "nick": member_verification_name(
            name=user.name,
            tid=user.tid,
            tag=user.faction.tag if user.faction is not None else "",
            name_template=guild.verify_template,
        ),
        "roles": set(str(role) for role in user_roles),
    }

    patch_json["roles"] -= invalid_member_faction_roles(
        faction_verify=guild.faction_verify,
        faction_id=user.faction_id,
    )
    patch_json["roles"] -= invalid_member_position_roles(
        faction_verify=guild.faction_verify,
        faction_id=user.faction_id,
        position=user.faction_position,
    )

    patch_json["roles"].update(member_verified_roles(verified_roles=guild.verified_roles))
    patch_json["roles"].update(member_faction_roles(faction_verify=guild.faction_verify, faction_id=user.faction_id))
    patch_json["roles"].update(
        member_position_roles(
            faction_verify=guild.faction_verify, faction_id=user.faction_id, position=user.faction_position
        )
    )

    if patch_json["nick"] == current_nick:
        patch_json.pop("nick")

    if patch_json["roles"] == set(user_roles):
        patch_json.pop("roles")
    else:
        patch_json["roles"] = list(patch_json["roles"])

    if len(patch_json) == 0 and (force is None or (isinstance(force, list) and not force.get("value"))):
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

    try:
        discordpatch(
            f"guilds/{guild.sid}/members/{user.discord_id}",
            patch_json,
        )
    except DiscordError as e:
        if e.code == 50013:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Verification Failed",
                            "description": "Discord prevents bots from modifying the roles and nickname of users that are the server owner or have a role higher than the bot's highest role. For more information, check out the [docs](https://docs.tornium.com/en/latest/user/bot/verification.html#verification).",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        raise e

    if user.faction is None:
        faction_str = "None"
    else:
        faction_str = f"{discord_escaper(user.faction.name)} [{user.faction.tid}]"

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Verification Successful",
                    "description": inspect.cleandoc(
                        f"""User: [{user.user_str_self()}](https://www.torn.com/profiles.php?XID={user.tid})
                        Faction: {faction_str}
                        Discord: <@{user.discord_id}>"""
                    ),
                    "color": SKYNET_GOOD,
                }
            ]
        },
    }
