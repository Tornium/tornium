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

import datetime

from peewee import DoesNotExist
from tornium_commons.models import ObanJob, Server
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_INFO

from skynet.decorators import invoker_required
from skynet.skyutils import get_admin_keys


@invoker_required
def verify_all(interaction, *args, **kwargs):
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

    try:
        guild: Server = (
            Server.select(
                Server.sid,
                Server.admins,
                Server.verify_template,
                Server.verified_roles,
                Server.faction_verify,
                Server.verify_enabled,
            )
            .where(Server.sid == interaction["guild_id"])
            .get()
        )
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

    if kwargs["invoker"].tid not in guild.admins:
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
                "flags": 64,
            },
        }
    elif not guild.verify_enabled:
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

    admin_keys = get_admin_keys(interaction, all_keys=True)

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

    verification_job: ObanJob = ObanJob.new(
        worker="Tornium.Workers.GuildVerification",
        queue="guild_processing",
        args={
            "guild_id": guild.sid,
            "after": 0,
        },
        tags=["guild"],
    )

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Verification Started",
                    "description": "Verification has started and will usually take a few minutes due to ratelimiting "
                    "by the Torn API, the Discord API, and Tornium. If a log channel is enabled, details will be sent "
                    "to it as verification proceeds.",
                    "color": SKYNET_INFO,
                    "footer": {"text": f"Task ID: #{verification_job.id}"},
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        },
    }
