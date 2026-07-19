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

import typing

from peewee import DoesNotExist
from tornium_commons.formatters import find_list
from tornium_commons.models import ObanJob, Server
from tornium_commons.skyutils import SKYNET_ERROR

from skynet.decorators import with_deferred_response


@with_deferred_response
def verify(interaction: dict, *args, **kwargs):
    try:
        guild: Server = Server.select().where(Server.sid == interaction["guild_id"]).get()
    except KeyError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Location",
                        "description": "The verification command must be run in a server where verification is setup "
                        "and enabled.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
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

    try:
        member_discord_id = int(find_list(interaction["data"]["options"], "name", "member")["value"])
    except Exception:
        member_discord_id = int(interaction["member"]["user"]["id"])

    try:
        # TODO: Remove from try/except once we can make sure this works in slash commands
        member_roles = interaction["data"]["resolved"]["members"][str(member_discord_id)]["roles"]

        if set(member_roles) & set(map(str, guild.exclusion_roles)):  # Exclusion role in member's roles
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
    except Exception:
        pass

    ObanJob.new(
        worker="Tornium.Workers.GuildMemberVerification",
        queue="guild_processing",
        args={
            "api_call_id": None,
            "guild_id": guild.sid,
            "member_id": member_discord_id,
            "token": interaction["token"],
        },
        tags=["guild"],
    )

    return None


@with_deferred_response
def verify_uc(interaction: dict, *args, **kwargs):
    try:
        guild: Server = Server.select().where(Server.sid == interaction["guild_id"]).get()
    except KeyError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Location",
                        "description": "The verification command must be run in a server where verification is setup "
                        "and enabled.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
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

    member_discord_id: int = int(interaction["data"]["target_id"])
    member_roles: typing.List[int] = interaction["data"]["resolved"]["members"][str(member_discord_id)]["roles"]

    if set(member_roles) & set(map(str, guild.exclusion_roles)):  # Exclusion role in member's roles
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

    ObanJob.new(
        worker="Tornium.Workers.GuildMemberVerification",
        queue="guild_processing",
        args={
            "api_call_id": None,
            "guild_id": guild.sid,
            "member_id": member_discord_id,
            "token": interaction["token"],
        },
        tags=["guild"],
    )

    return None
