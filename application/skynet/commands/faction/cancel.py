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

from peewee import DoesNotExist
from tornium_celery.tasks.api import discordpatch, discordpost
from tornium_commons.formatters import commas, discord_escaper, find_list
from tornium_commons.models import Server, User, Withdrawal
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from skynet.decorators import invoker_required
from skynet.skyutils import get_admin_keys


@invoker_required
def cancel_command(interaction, *args, **kwargs):
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

    requester: typing.Optional[User]
    try:
        requester = User.get_by_id(withdrawal.requester)
    except DoesNotExist:
        requester = None

    discordpatch(
        f"channels/{guild.banking_config[str(user.faction_id)]['channel']}/messages/{withdrawal.withdrawal_message}",
        {
            "embeds": [
                {
                    "title": f"Vault Request #{withdrawal_id}",
                    "description": f"This request has been cancelled by {discord_escaper(user.name)} [{user.tid}].",
                    "fields": [
                        {
                            "name": "Original Request Amount",
                            "value": f"{commas(withdrawal.amount)} {'Cash' if withdrawal.cash_request else 'Points'}",
                        },
                        {
                            "name": "Original Requester",
                            "value": (
                                f"N/A [{withdrawal.requester}]" if requester is None else requester.user_str_self()
                            ),
                        },
                    ],
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "color": SKYNET_ERROR,
                }
            ],
            "components": [],
        },
    )

    Withdrawal.update(status=2, fulfiller=user.tid, time_fulfilled=datetime.datetime.utcnow()).where(
        Withdrawal.wid == withdrawal.wid
    ).execute()

    if requester.discord_id not in (None, 0):
        try:
            dm_channel = discordpost("users/@me/channels", payload={"recipient_id": requester.discord_id})
        except Exception:
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

        discordpost.delay(
            f"channels/{dm_channel['id']}/messages",
            payload={
                "embeds": [
                    {
                        "title": "Vault Request Cancelled",
                        "description": f"Your vault request #{withdrawal.wid} has been cancelled by {discord_escaper(user.name)} [{user.tid}]",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        ).forget()

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

    requester: typing.Optional[User]
    try:
        requester = User.get_by_id(withdrawal.requester)
    except DoesNotExist:
        requester = None

    discordpatch(
        f"channels/{guild.banking_config[str(user.faction_id)]['channel']}/messages/{withdrawal.withdrawal_message}",
        {
            "embeds": [
                {
                    "title": f"Vault Request #{withdrawal.wid}",
                    "description": f"This request has been cancelled by {discord_escaper(user.name)} [{user.tid}].",
                    "fields": [
                        {
                            "name": "Original Request Amount",
                            "value": f"{commas(withdrawal.amount)} {'Cash' if withdrawal.cash_request else 'Points'}",
                        },
                        {
                            "name": "Original Requester",
                            "value": (
                                f"N/A [{withdrawal.requester}]" if requester is None else requester.user_str_self()
                            ),
                        },
                    ],
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "color": SKYNET_ERROR,
                }
            ],
            "components": [],
        },
    )

    Withdrawal.update(status=2, fulfiller=user.tid, time_fulfilled=datetime.datetime.utcnow()).where(
        Withdrawal.wid == withdrawal.wid
    ).execute()

    if requester.discord_id not in (None, 0):
        try:
            dm_channel = discordpost("users/@me/channels", payload={"recipient_id": requester.discord_id})
        except Exception:
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

        discordpost.delay(
            f"channels/{dm_channel['id']}/messages",
            payload={
                "embeds": [
                    {
                        "title": "Vault Request Cancelled",
                        "description": f"Your vault request #{withdrawal.wid} has been cancelled by {discord_escaper(user.name)} [{user.tid}]",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        ).forget()

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
