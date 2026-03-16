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
import typing

from peewee import DoesNotExist
from tornium_celery.tasks.api import discordpatch, discordpost
from tornium_commons.formatters import commas, discord_escaper, find_list
from tornium_commons.models import Server, User, Withdrawal
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from skynet.decorators import invoker_required
from skynet.skyutils import get_admin_keys


@invoker_required
def cancel_command(interaction, *args, **kwargs):
    user: User = kwargs["invoker"]
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

    if user.faction is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Not Located",
                        "description": "Your faction could not be located in Tornium's database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction.guild is None or user.faction_id not in user.faction.guild.factions:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The server needs to be added to {discord_escaper(user.faction.name)}'s bot configuration and "
                        f"to the server. Please contact the server administrators for the faction's server to do this via "
                        f"[the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }
    elif (
        str(user.faction_id) not in user.faction.guild.banking_config
        or user.faction.guild.banking_config[str(user.faction_id)]["channel"] == "0"
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The banking channels needs to be set for {discord_escaper(user.faction.name)}. Please contact "
                        f"the server administrators for the faction's server to do this via [the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }

    if "options" in interaction["data"]:
        withdrawal_id = find_list(interaction["data"]["options"], "name", "id")
    else:
        withdrawal_id = None

    if withdrawal_id is not None:
        withdrawal_id = withdrawal_id["value"]
    if withdrawal_id is not None and user.tid not in user.faction.get_bankers():
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "Only faction members with banking permissions are allowed to cancel banking "
                        "requests.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        withdrawal: Withdrawal
        if withdrawal_id is None:
            withdrawal = (
                Withdrawal.select().where(Withdrawal.requester == user.tid).order_by(-Withdrawal.time_requested).get()
            )
        else:
            withdrawal = Withdrawal.select().where(Withdrawal.wid == withdrawal_id).get()
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Does not Exist",
                        "description": f"Vault Request #{withdrawal_id} does not currently exist.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    if withdrawal.faction_tid != user.faction_id:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "You may only cancel requests for your faction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif withdrawal.status == 1:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Fulfilled",
                        "description": f"Vault Request #{withdrawal.wid} has already been fulfilled by "
                        f"{User.user_str(withdrawal.fulfiller)} <t:{int(withdrawal.time_fulfilled.timestamp())}:R>.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif withdrawal.status == 2:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Cancelled",
                        "description": f"Vault Request #{withdrawal.wid} has already been cancelled by "
                        f"{User.user_str(withdrawal.fulfiller)} <t:{int(withdrawal.time_fulfilled.timestamp())}:R>.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif withdrawal.status == 3:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Cancelled",
                        "description": f"Vault Request #{withdrawal.wid} has already been cancelled by the system "
                        f"<t:{int(withdrawal.time_fulfilled.timestamp())}:R>.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    withdrawal.cancel(user)

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Banking Request Cancelled",
                    "description": f"You have cancelled banking request #{withdrawal.wid}.",
                    "color": SKYNET_GOOD,
                }
            ],
            "flags": 64,
        },
    }


@invoker_required
def cancel_button(interaction, *args, **kwargs):
    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Allowed",
                        "description": "This command can not be run in a DM (for now).",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif interaction["data"]["custom_id"] != "faction:vault:cancel" or interaction["data"]["component_type"] != 2:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Unknown Button Press",
                        "description": "The attributes of the button pressed does not match the attributes required.",
                        "color": SKYNET_ERROR,
                    }
                ]
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

    user: User = kwargs["invoker"]
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

    if user.faction is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Not Located",
                        "description": "Your faction could not be located in Tornium's database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction_id not in guild.factions or user.faction.guild_id != guild.sid:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The server needs to be added to {discord_escaper(user.faction.name)}'s bot configuration and "
                        f"to the server. Please contact the server administrators to do this via "
                        f"[the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }
    elif user.tid not in user.faction.get_bankers():
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "Only faction members with banking permissions are allowed to cancel banking "
                        "requests.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif (
        str(user.faction_id) not in guild.banking_config or guild.banking_config[str(user.faction_id)]["channel"] == "0"
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The banking channels needs to be set for {discord_escaper(user.faction.name)}. Please contact "
                        f"the server administrators to do this via [the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }

    try:
        withdrawal: Withdrawal = (
            Withdrawal.select().where(Withdrawal.withdrawal_message == interaction["message"]["id"]).get()
        )
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Does Not Exist",
                        "description": "The Vault Request does not currently exist.",
                        "color": SKYNET_ERROR,
                        "footer": {"text": f"Message ID: {interaction['message']['id']}"},
                    }
                ],
                "flags": 64,
            },
        }

    if withdrawal.faction_tid != user.faction_id:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "You may only cancel requests for your faction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif withdrawal.status == 1:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Fulfilled",
                        "description": f"Vault Request #{withdrawal.wid} has already been fulfilled by "
                        f"{User.user_str(withdrawal.fulfiller)} <t:{int(withdrawal.time_fulfilled.timestamp())}:R>.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif withdrawal.status == 2:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Cancelled",
                        "description": f"Vault Request #{withdrawal.wid} has already been cancelled by "
                        f"{User.user_str(withdrawal.fulfiller)} <t:{int(withdrawal.time_fulfilled.timestamp())}:R>.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif withdrawal.status == 3:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Cancelled",
                        "description": f"Vault Request #{withdrawal.wid} has already been cancelled by the system "
                        f"<t:{int(withdrawal.time_fulfilled.timestamp())}:R>.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    withdrawal.cancel(user)

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Banking Request Cancelled",
                    "description": f"You have cancelled banking request #{withdrawal.wid}.",
                    "color": SKYNET_GOOD,
                }
            ],
            "flags": 64,
        },
    }
