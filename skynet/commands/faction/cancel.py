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
import random

import tasks
import utils
from models.faction import Faction
from models.server import Server
from models.user import User
from models.usermodel import UserModel
from models.withdrawalmodel import WithdrawalModel
from skynet.skyutils import SKYNET_ERROR, SKYNET_GOOD, get_admin_keys, invoker_exists


@invoker_exists
def cancel_command(interaction, *args, **kwargs):
    print(interaction)

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

    server = Server(interaction["guild_id"])
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

    try:
        user: User = User(user.tid)
        user.refresh(key=random.choice(admin_keys))

        if user.factiontid == 0:
            user.refresh(key=random.choice(admin_keys), force=True)

            if user.factiontid == 0:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Faction ID Error",
                                "description": f"The faction ID of {interaction['message']['user']['username']} is not "
                                f"set regardless of a force refresh.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,  # Ephemeral
                    },
                }
    except utils.errors.MissingKeyError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Key Available",
                        "description": "No Torn API key could be utilized for this request.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    faction = Faction(user.factiontid)

    if user.factiontid not in server.factions:
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
    elif user.tid not in faction.get_bankers():
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

    if (
        faction.vault_config.get("banking") in [0, None]
        or faction.vault_config.get("banker") in [0, None]
        or faction.config.get("vault") in [0, None]
    ):
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

    withdrawal_id = utils.find_list(interaction["data"]["options"], "name", "id")

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
        withdrawal: WithdrawalModel = WithdrawalModel.objects(requester=faction.tid).order_by("-time_requested").first()
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
    elif withdrawal.fulfiller > 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Fulfilled",
                        "description": f"Vault Request #{withdrawal.wid} has already been fulfilled by "
                        f"{User(withdrawal.fulfiller).name} at {utils.torn_timestamp(withdrawal.time_fulfilled)}.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif withdrawal.fulfiller < 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Cancelled",
                        "description": f"Vault Request #{withdrawal.wid} has already been cancelled by "
                        f"{User(-withdrawal.fulfiller).name} at {utils.torn_timestamp(withdrawal.time_fulfilled)}.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    try:
        tasks.discordpatch(
            f"channels/{faction.vault_config['banking']}/messages/{withdrawal.withdrawal_message}",
            {
                "embeds": [
                    {
                        "title": f"Vault Request #{withdrawal_id}",
                        "description": f"This request has been fulfilled by {user.name} [{user.tid}].",
                        "fields": [
                            {
                                "name": "Original Request Amount",
                                "value": utils.commas(withdrawal.amount),
                            },
                            {
                                "name": "Original Request Type",
                                "value": "Points" if withdrawal.wtype == 1 else "Cash",
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
                                "url": f"https://tornium.com/faction/banking/fulfill/{withdrawal_id}",
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
    except utils.DiscordError as e:
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
    except utils.NetworkingError as e:
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
    withdrawal.time_fulfilled = utils.now()
    withdrawal.save()

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


@invoker_exists
def cancel_button(interaction, *args, **kwargs):
    print(interaction)

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

    server = Server(interaction["guild_id"])
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

    try:
        user: User = User(user.tid)
        user.refresh(key=random.choice(admin_keys))

        if user.factiontid == 0:
            user.refresh(key=random.choice(admin_keys), force=True)

            if user.factiontid == 0:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Faction ID Error",
                                "description": f"The faction ID of {interaction['message']['user']['username']} is not "
                                f"set regardless of a force refresh.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,  # Ephemeral
                    },
                }
    except utils.MissingKeyError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Key Available",
                        "description": "No Torn API key could be utilized for this request.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    faction = Faction(user.factiontid)

    if user.factiontid not in server.factions:
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
    elif user.tid not in faction.get_bankers():
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

    if (
        faction.vault_config.get("banking") in [0, None]
        or faction.vault_config.get("banker") in [0, None]
        or faction.config.get("vault") in [0, None]
    ):
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
    elif withdrawal.fulfiller > 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Fulfilled",
                        "description": f"Vault Request #{withdrawal.wid} has already been fulfilled by "
                        f"{User(withdrawal.fulfiller).name} at {utils.torn_timestamp(withdrawal.time_fulfilled)}.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif withdrawal.fulfiller < 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Cancelled",
                        "description": f"Vault Request #{withdrawal.wid} has already been cancelled by "
                        f"{User(-withdrawal.fulfiller).name} at {utils.torn_timestamp(withdrawal.time_fulfilled)}.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    try:
        tasks.discordpatch(
            f"channels/{faction.vault_config['banking']}/messages/{withdrawal.withdrawal_message}",
            {
                "embeds": [
                    {
                        "title": f"Vault Request #{withdrawal.wid}",
                        "description": f"This request has been cancelled by {user.name} [{user.tid}].",
                        "fields": [
                            {
                                "name": "Original Request Amount",
                                "value": utils.commas(withdrawal.amount),
                            },
                            {
                                "name": "Original Request Type",
                                "value": "Points" if withdrawal.wtype == 1 else "Cash",
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
                                "url": f"https://tornium.com/faction/banking/fulfill/{withdrawal.wid}",
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
    except utils.DiscordError as e:
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
    except utils.NetworkingError as e:
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
    withdrawal.time_fulfilled = utils.now()
    withdrawal.save()

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
