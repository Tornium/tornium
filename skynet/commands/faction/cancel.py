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
import time
import typing

from tornium_celery.tasks.api import discordpatch, discordpost
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.formatters import commas, find_list, torn_timestamp
from tornium_commons.models import FactionModel, ServerModel, UserModel, WithdrawalModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from models.faction import Faction
from models.user import User
from skynet.commands.faction.fulfill import fulfiller_string
from skynet.skyutils import get_admin_keys


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
                "flags": 64,  # Ephemeral
            },
        }

    server = ServerModel.objects(sid=interaction["guild_id"]).first()

    if server is None:
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
                "flags": 64,  # Ephemeral
            },
        }

    user: UserModel = kwargs["invoker"]
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

    faction = FactionModel.objects(tid=user.factionid).first()

    if faction is None:
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
                "flags": 64,  # Ephemeral
            },
        }
    elif user.factionid not in server.factions or faction.guild != server.sid:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The server needs to be added to {faction.name}'s bot configuration and to the "
                        f"server. Please contact the server administrators to do this via "
                        f"[the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }
    elif user.tid not in Faction(faction.tid).get_bankers():
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
                "flags": 64,  # Ephemeral
            },
        }
    elif str(faction.tid) not in server.banking_config or server.banking_config[str(faction.tid)]["channel"] == "0":
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The banking channels needs to be set for {faction.name}. Please contact "
                        f"the server administrators to do this via "
                        f"[the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }

    if "options" in interaction["data"]:
        withdrawal_id = find_list(interaction["data"]["options"], "name", "id")
    else:
        withdrawal_id = -1

    if withdrawal_id != -1:
        withdrawal_id = withdrawal_id[1]["value"]

    if type(withdrawal_id) == str and not withdrawal_id.isdigit():
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
                "flags": 64,  # Ephemeral
            },
        }

    if withdrawal_id == -1:
        withdrawal: WithdrawalModel = WithdrawalModel.objects(requester=user.tid).order_by("-time_requested").first()
    else:
        withdrawal: WithdrawalModel = WithdrawalModel.objects(wid=int(withdrawal_id)).first()

    if withdrawal is None:
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
                "flags": 64,  # Ephemeral
            },
        }
    elif withdrawal.fulfiller != 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Unable to Cancel Request",
                        "description": f"Vault Request #{withdrawal.wid} {fulfiller_string(withdrawal)} <t:{withdrawal.time_fulfilled}:R>.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    requester: typing.Optional[UserModel] = UserModel.objects(tid=withdrawal.requester).first()

    try:
        discordpatch(
            f"channels/{server.banking_config[str(faction.tid)]['channel']}/messages/{withdrawal.withdrawal_message}",
            {
                "embeds": [
                    {
                        "title": f"Vault Request #{withdrawal_id}",
                        "description": f"This request has been cancelled by {user.name} [{user.tid}].",
                        "fields": [
                            {
                                "name": "Original Request Amount",
                                "value": commas(withdrawal.amount),
                            },
                            {
                                "name": "Original Request Type",
                                "value": "Points" if withdrawal.wtype == 1 else "Cash",
                            },
                            {
                                "name": "Original Requester",
                                "value": f"{'Unknown' if requester is None else requester.name} [{withdrawal.requester}]",
                            },
                        ],
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "color": SKYNET_ERROR,
                    }
                ],
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Faction Vault",
                                "url": "https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user",
                            },
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Fulfill",
                                "url": f"https://tornium.com/faction/banking/fulfill/{withdrawal.guid}",
                            },
                            {
                                "type": 2,
                                "style": 3,
                                "label": "Fulfill Manually",
                                "custom_id": "faction:vault:fulfill",
                            },
                            {
                                "type": 2,
                                "style": 4,
                                "label": "Cancel",
                                "custom_id": "faction:vault:cancel",
                            },
                        ],
                    }
                ],
            },
        )
    except DiscordError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Discord API Error",
                        "description": "The Discord API has returned an error.",
                        "fields": [
                            {"name": "Error Code", "value": e.code},
                            {"name": "Error Message", "value": e.message},
                        ],
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    except NetworkingError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Discord Networking Error",
                        "description": "The Discord API has returned an HTTP error.",
                        "fields": [
                            {"name": "HTTP Error Code", "value": e.code},
                            {"name": "HTTP Error Message", "value": e.message},
                        ],
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    withdrawal.fulfiller = -user.tid
    withdrawal.time_fulfilled = int(time.time())
    withdrawal.save()

    if requester.discord_id not in (None, "", 0):
        try:
            dm_channel = discordpost("users/@me/channels", payload={"recipient_id": requester.discord_id})
        except Exception:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Banking Request {withdrawal.wid} Fulfilled",
                            "description": "You have fulfilled the banking request.",
                            "color": SKYNET_GOOD,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        discordpost.delay(
            f"channels/{dm_channel['id']}/messages",
            payload={
                "embeds": [
                    {
                        "title": "Vault Request Cancelled",
                        "description": f"Your vault request #{withdrawal.wid} has been cancelled by {user.name} [{user.tid}]",
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
                    "title": f"Banking Request {withdrawal_id} Cancelled",
                    "description": "You have cancelled the banking request.",
                    "color": SKYNET_GOOD,
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }


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
                "flags": 64,  # Ephemeral
            },
        }

    server = ServerModel.objects(sid=interaction["guild_id"]).first()

    if server is None:
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
                "flags": 64,  # Ephemeral
            },
        }

    user: UserModel = kwargs["invoker"]
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

    faction = FactionModel.objects(tid=user.factionid).first()

    if faction is None:
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
                "flags": 64,  # Ephemeral
            },
        }
    elif user.factionid not in server.factions or faction.guild != server.sid:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The server needs to be added to {faction.name}'s bot configuration and to the "
                        f"server. Please contact the server administrators to do this via "
                        f"[the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }
    elif user.tid not in Faction(faction.tid).get_bankers():
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
                "flags": 64,  # Ephemeral
            },
        }
    elif str(faction.tid) not in server.banking_config or server.banking_config[str(faction.tid)]["channel"] == "0":
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The banking channels needs to be set for {faction.name}. Please contact "
                        f"the server administrators to do this via "
                        f"[the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
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

    withdrawal: WithdrawalModel = WithdrawalModel.objects(withdrawal_message=interaction["message"]["id"]).first()

    if withdrawal is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Does not Exist",
                        "description": "The Vault Request does not currently exist.",
                        "color": SKYNET_ERROR,
                        "footer": {"text": f"Message ID: {interaction['message']['id']}"},
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif withdrawal.fulfiller != 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Unable to Cancel Request",
                        "description": f"Vault Request #{withdrawal.wid} {fulfiller_string(withdrawal)} <t:{withdrawal.time_fulfilled}:R>.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    requester: typing.Optional[UserModel] = UserModel.objects(tid=withdrawal.requester).first()

    try:
        discordpatch(
            f"channels/{server.banking_config[str(faction.tid)]['channel']}/messages/{withdrawal.withdrawal_message}",
            {
                "embeds": [
                    {
                        "title": f"Vault Request #{withdrawal.wid}",
                        "description": f"This request has been cancelled by {user.name} [{user.tid}].",
                        "fields": [
                            {
                                "name": "Original Request Amount",
                                "value": commas(withdrawal.amount),
                            },
                            {
                                "name": "Original Request Type",
                                "value": "Points" if withdrawal.wtype == 1 else "Cash",
                            },
                            {
                                "name": "Original Requester",
                                "value": f"{'Unknown' if requester is None else requester.name} [{withdrawal.requester}]",
                            },
                        ],
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "color": SKYNET_ERROR,
                    }
                ],
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Faction Vault",
                                "url": "https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user",
                            },
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Fulfill",
                                "url": f"https://tornium.com/faction/banking/fulfill/{withdrawal.guid}",
                            },
                            {
                                "type": 2,
                                "style": 3,
                                "label": "Fulfill Manually",
                                "custom_id": "faction:vault:fulfill",
                            },
                            {
                                "type": 2,
                                "style": 4,
                                "label": "Cancel",
                                "custom_id": "faction:vault:cancel",
                            },
                        ],
                    }
                ],
            },
        )
    except DiscordError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Discord API Error",
                        "description": "The Discord API has returned an error.",
                        "fields": [
                            {"name": "Error Code", "value": e.code},
                            {"name": "Error Message", "value": e.message},
                        ],
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    except NetworkingError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Discord Networking Error",
                        "description": "The Discord API has returned an HTTP error.",
                        "fields": [
                            {"name": "HTTP Error Code", "value": e.code},
                            {"name": "HTTP Error Message", "value": e.message},
                        ],
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    withdrawal.fulfiller = -user.tid
    withdrawal.time_fulfilled = int(time.time())
    withdrawal.save()

    if requester.discord_id not in (None, "", 0):
        try:
            dm_channel = discordpost("users/@me/channels", payload={"recipient_id": requester.discord_id})
        except Exception:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Banking Request {withdrawal.wid} Fulfilled",
                            "description": "You have fulfilled the banking request.",
                            "color": SKYNET_GOOD,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        discordpost.delay(
            f"channels/{dm_channel['id']}/messages",
            payload={
                "embeds": [
                    {
                        "title": "Vault Request Fulfilled",
                        "description": f"Your vault request #{withdrawal.wid} has been fulfilled by {user.name} [{user.tid}]",
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
                    "title": f"Banking Request {withdrawal.wid} Cancelled",
                    "description": "You have cancelled the banking request.",
                    "color": SKYNET_GOOD,
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }
