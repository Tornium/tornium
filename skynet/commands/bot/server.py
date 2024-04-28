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

from peewee import DoesNotExist, ProgrammingError, fn
from tornium_commons.models import Faction, Server, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from skynet.decorators import invoker_required


@invoker_required
def link_server(interaction, subcommand_data, *args, **kwargs):
    user: User = kwargs["invoker"]

    if interaction.get("guild_id") in (None, 0):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Server ID",
                        "description": "This command must be run within a server",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }

    if user is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Not Found",
                        "description": "This user could not be found in the database. Try verifying yourself or signing into [Tornium](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction_id is None or not user.faction_aa:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "Only AA members of factions are allowed to run this command.",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }
    elif user.faction.guild_id is not None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Already Linked",
                        "description": "This faction is already linked to a server. You'll need to unlink the faction first before re-linking it.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    Faction.update(guild=interaction["guild_id"]).where(User.faction.tid == user.faction_id).execute()

    try:
        server = Server.select(Server.admins, Server.factions).where(Server.sid == interaction["guild_id"]).get()
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Not Found",
                        "description": "This server could not be found in the database.",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }

    if user.tid not in server.admins or user.faction_id in server.factions:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Linked",
                        "description": f"{user.faction.name} [{user.faction_id}] has been linked to this server. If a server admin has not already done so, they will need to add your faction to the server's list of factions.",
                        "color": SKYNET_GOOD,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        Server.update(factions=fn.array_append(user.faction_id)).where(Server.sid == user.faction.guild_id).execute()
    except ProgrammingError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Linked",
                        "description": f"{user.faction.name} [{user.faction_id}] has been linked to this server. If a server admin has not already done so, they will need to add your faction to the server's list of factions.",
                        "color": SKYNET_GOOD,
                    }
                ],
                "flags": 64,
            },
        }

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Faction and Server Linked",
                    "description": f"{user.faction.name} [{user.faction_id}] has been linked to this server. Since you're also a server admin, this faction has been added to the server's list of factions.",
                    "color": SKYNET_GOOD,
                }
            ],
            "flags": 64,
        },
    }


@invoker_required
def unlink_server(interaction, subcommand_data, *args, **kwargs):
    user: User = kwargs["invoker"]

    if user is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Not Found",
                        "description": "This user could not be found in the database. Try verifying yourself or signing into [Tornium](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction_id is None or not user.faction_aa:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "Only AA members of factions are allowed to run this command.",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }
    elif user.faction.guild_id is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Not Linked",
                        "description": "This faction is not already linked to a server.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    Faction.update(guild=None).where(User.faction.tid == user.faction_id).execute()

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Faction Unlinked",
                    "description": f"{user.faction.name} [{user.faction_id}] has been unlinked to their previous server.",
                    "color": SKYNET_GOOD,
                }
            ],
            "flags": 64,
        },
    }


def server_config_switchboard(interaction, *args, **kwargs):
    try:
        subcommand = interaction["data"]["options"][0]["name"]
        subcommand_data = interaction["data"]["options"][0]["options"]
    except Exception:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Interaction Format",
                        "description": "Discord has returned an invalidly formatted interaction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    if subcommand == "link":
        return link_server(interaction, subcommand_data, *args, **kwargs)
    elif subcommand == "unlink":
        return unlink_server(interaction, subcommand_data, *args, **kwargs)
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Command Not Found",
                        "description": "This command does not exist.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
