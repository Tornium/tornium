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
import typing

from tornium_celery.tasks.guild import verify_users
from tornium_commons.formatters import find_list
from tornium_commons.models import ServerModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_INFO

from skynet.skyutils import get_admin_keys


def verifyall(interaction, *args, **kwargs):
    if int(interaction["guild_id"]) != 701115188924907600:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Command Disabled",
                        "description": "This command has been disabled pending re-implemenation.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Location",
                        "description": "The verification command must be run in a server where verification is set up "
                        "and enabled.",
                    }
                ],
                "flags": 64,
            },
        }

    guild: typing.Optional[ServerModel] = ServerModel.objects(sid=interaction["guild_id"]).first()

    if guild is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Unknown Server",
                        "description": "This server could not be found in the database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif kwargs["invoker"].tid not in guild.admins:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "Only server admins are allowed to run this command",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif guild.config.get("verify") in (None, 0):
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
                "flags": 64,  # Ephemeral
            },
        }

    if "options" in interaction["data"]:
        force = find_list(interaction["data"]["options"], "name", "force")
    else:
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

    task = verify_users.delay(
        guild_id=guild.sid,
        admin_keys=admin_keys,
        force=force,
    )
    task_id = task.id
    task.forget()

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Verification Started",
                    "description": "Verification has started and will usually take a few minutes due to ratelimiting "
                    "by the Torn API and Tornium. If a log channel is enabled, details will be sent "
                    "to it as verification proceeds.",
                    "color": SKYNET_INFO,
                    "footer": {"text": f"Task ID: {task_id}"},
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        },
    }
