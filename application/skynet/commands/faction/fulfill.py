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

from peewee import DoesNotExist
from tornium_celery.tasks.api import discordpatch
from tornium_celery.tasks.misc import send_dm
from tornium_commons.formatters import discord_escaper, find_list
from tornium_commons.models import Server, User, Withdrawal
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from skynet.decorators import invoker_required


@invoker_required
def fulfill_command(interaction, *args, **kwargs):
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

    withdrawal_id = find_list(interaction["data"]["options"], "name", "id")

    if withdrawal_id is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameters Passed",
                        "description": "No withdrawal ID was passed, but is required.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    if "options" in interaction["data"]:
        withdrawal_id = find_list(interaction["data"]["options"], "name", "id")
    else:
        withdrawal_id = None

    if withdrawal_id is not None:
        withdrawal_id = withdrawal_id["value"]

    try:
        withdrawal_id = int(withdrawal_id)
    except (TypeError, ValueError):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameter Value",
                        "description": "An illegal withdrawal ID type was passed. The withdrawal ID must be an integer.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        withdrawal: Withdrawal = Withdrawal.select().where(Withdrawal.wid == withdrawal_id).get()
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Does Not Exist",
                        "description": f"Vault Request #{withdrawal_id} does not currently exist.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        updated_withdrawal: Withdrawal = withdrawal.fulfill(user.tid, user.user_str_self(), discordpatch, send_dm)

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Banking Request Fulfilled",
                        "description": f"You have fulfilled banking request #{updated_withdrawal.wid}.",
                        "color": SKYNET_GOOD,
                    }
                ],
                "flags": 64,
            },
        }
    except (DoesNotExist, IndexError):
        # If the updated withdrawal does not exist, some condition in the where clause failed.
        # We can just continue and expect a proper updated withdrawal to be handled inside of
        # the try clause, but we will want to re-fetch the withdrawal in case it's stale due to
        # another fulfillment in parallel.
        withdrawal: Withdrawal = Withdrawal.select().where(Withdrawal.wid == withdrawal_id).get()

    if withdrawal.status == 1:
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

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Unable to Fulfill Request",
                    "description": f"Vault Request #{withdrawal.wid} could not be fulfilled due to an unhandled error. "
                    "Please create a ticket on Tornium's Discord server.",
                    "color": SKYNET_ERROR,
                }
            ]
        },
    }


@invoker_required
def fulfill_button(interaction, *args, **kwargs):
    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Allowed",
                        "description": "This button can not be run in a DM.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif interaction["data"]["custom_id"] != "faction:vault:fulfill" or interaction["data"]["component_type"] != 2:
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

    try:
        updated_withdrawal: Withdrawal = withdrawal.fulfill(user.tid, user.user_str_self(), discordpatch, send_dm)

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Banking Request Fulfilled",
                        "description": f"You have fulfilled banking request #{updated_withdrawal.wid}.",
                        "color": SKYNET_GOOD,
                    }
                ],
                "flags": 64,
            },
        }
    except (DoesNotExist, IndexError):
        # If the updated withdrawal does not exist, some condition in the where clause failed.
        # We can just continue and expect a proper updated withdrawal to be handled inside of
        # the try clause, but we will want to re-fetch the withdrawal in case it's stale due to
        # another fulfillment in parallel.
        withdrawal: Withdrawal = (
            Withdrawal.select().where(Withdrawal.withdrawal_message == interaction["message"]["id"]).get()
        )

    if withdrawal.status == 1:
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

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Unable to Fulfill Request",
                    "description": f"Vault Request #{withdrawal.wid} could not be fulfilled due to an unhandled error. "
                    "Please create a ticket on Tornium's Discord server.",
                    "color": SKYNET_ERROR,
                }
            ]
        },
    }
