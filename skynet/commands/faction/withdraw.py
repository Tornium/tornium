# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import random

from bot import botutils
from models.faction import Faction
from models.server import Server
from models.user import User
from models.usermodel import UserModel
from models.withdrawalmodel import WithdrawalModel
import redisdb
import tasks
import utils


def withdraw(interaction):
    print(interaction)
    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Allowed",
                        "description": "This command can not be run in a DM (for now).",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    server = Server(interaction["guild_id"])

    if "member" in interaction:
        user: UserModel = UserModel.objects(
            discord_id=interaction["member"]["user"]["id"]
        ).first()
    else:
        user: UserModel = UserModel.objects(
            discord_id=interaction["user"]["id"]
        ).first()

    if "options" not in interaction["data"]:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Withdrawal Request Failed",
                        "description": "No options were passed with the "
                        "request. The withdrawal amount option is required.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    # -1: default
    # 0: cash (default)
    # 1: points
    withdrawal_option = utils.find_list(
        interaction["data"]["options"], "name", "option"
    )

    if withdrawal_option == -1:
        withdrawal_option = 0
    elif withdrawal_option[1]["value"] == "Cash":
        withdrawal_option = 0
    elif withdrawal_option[1]["value"] == "Points":
        withdrawal_option = 1
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Withdrawal Request Failed",
                        "description": "An incorrect withdrawal type was passed.",
                        "color": 0xC83F49,
                        "footer": {
                            "text": f"Inputted withdrawal type: {withdrawal_option[1]['value']}"
                        },
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if user is None:
        if server is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Error",
                            "description": "Your user could not be located in Tornium's databases. Please run this "
                            "command in a server with the Tornium bot or sign into "
                            "[Tornium](https://torn.deek.sh/login).",
                            "color": 0xC83F49,
                        }
                    ]
                },
            }
        elif len(server.admins) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No Admins",
                            "description": "There are no admins currently signed into Tornium.",
                            "color": 0xC83F49,
                        }
                    ]
                },
            }

        admin_id = random.choice(server.admins)
        admin: UserModel = UserModel.objects(tid=admin_id).first()

        if admin is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Admin Not Found",
                            "description": "Admin not found in the database. Please try again.",
                            "color": 0xC83F49,
                            "footer": {"text": f"Unknown Admin ID: {admin_id}"},
                        }
                    ]
                },
            }
        elif admin.key in ("", None):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Admin Key Not Found",
                            "description": "Admin located in the database, but the admin's key was not found. Please "
                            "try again.",
                            "color": 0xC83F49,
                            "footer": {"text": f"Borked Admin ID: {admin_id}"},
                        }
                    ]
                },
            }

        try:
            user_data = tasks.tornget(
                f"user/{interaction['member']['user']['id']}?selections=profile,discord", admin.key
            )
        except utils.TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Torn API Error",
                            "description": f'The Torn API has raised error code {e.code}: "{e.message}".',
                            "color": 0xC83F49,
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
                            "title": "HTTP Error",
                            "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        user = UserModel(
            tid=user_data["player_id"],
            name=user_data["name"],
            level=user_data["level"],
            last_refresh=utils.now(),
            discord_id=user_data["discord"]["discordID"]
            if user_data["discord"]["discordID"] != ""
            else 0,
            factionid=user_data["faction"]["faction_id"],
            status=user_data["last_action"]["status"],
            last_action=user_data["last_action"]["timestamp"],
        )
        user.save()

        if user.discord_id == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "User Requires Verification",
                            "description": "You are required to be verified officially by Torn through the "
                            "[official Torn Discord server](https://www.torn.com/discord] before being "
                            "able to utilize the banking features of this bot. Alternatively, you can "
                            "sign into [the web dashboard](https://torn.deek.sh/faction/banking) with "
                            "your API key to send a request without verifying. If you have recently "
                            "verified yourself, please wait a minute or two before trying again.",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
    elif user.tid == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Requires Verification",
                        "description": "You are required to be verified officially by Torn through the "
                        "[official Torn Discord server](https://www.torn.com/discord] before being "
                        "able to utilize the banking features of this bot. Alternatively, you can "
                        "sign into [the web dashboard](https://torn.deek.sh/faction/banking) with "
                        "your API key to send a request without verifying. If you have recently "
                        "verified yourself, please wait a minute or two before trying again.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    try:
        user: User = User(user.tid)
        if server is None:
            user.refresh()
        else:
            user.refresh(key=User(random.choice(server.admins)).key)

        if user.factiontid == 0:
            if server is None:
                user.refresh(force=True)
            else:
                user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Faction ID Error",
                                "description": f"The faction ID of {interaction['message']['user']['username']} is not "
                                f"set regardless of a force refresh.",
                                "color": 0xC83F49,
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
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    client = redisdb.get_redis()

    if client.get(f"tornium:banking-ratelimit:{user.tid}") is not None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Ratelimit Reached",
                        "description": f"You have reached the ratelimit on banking requests (once every minute). "
                        f"Please try again in {client.ttl(f'tornium:banking-ratelimit:{user.tid}')} seconds.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    else:
        client.set(f"tornium:banking-ratelimit:{user.tid}", 1)
        client.expire(f"tornium:banking-ratelimit:{user.tid}", 60)

    withdrawal_amount = utils.find_list(
        interaction["data"]["options"], "name", "amount"
    )

    if withdrawal_amount == -1:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameters Passed",
                        "description": "No withdrawal amount was passed, but is required.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    withdrawal_amount = withdrawal_amount[1]["value"]

    if type(withdrawal_amount) == str:
        if withdrawal_amount.lower() == "all":
            withdrawal_amount = "all"
        else:
            withdrawal_amount = botutils.text_to_num(withdrawal_amount)

    faction = Faction(user.factiontid)

    if user.factiontid not in server.factions:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The server needs to be added to {faction.name}'s bot configration and to the "
                        f"server. Please contact the server administrators to do this via "
                        f"[the dashboard](https://torn.deek.sh).",
                        "color": 0xC83F49,
                    }
                ]
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
                        "description": f"The server needs to be added to {faction.name}'s bot configration and to the "
                        f"server. Please contact the server administrators to do this via "
                        f"[the dashboard](https://torn.deek.sh).",
                        "color": 0xC83F49,
                    }
                ]
            },
        }

    try:
        faction_balances = tasks.tornget(
            f"faction/?selections=donations", faction.rand_key()
        )
    except utils.TornError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Torn API Error",
                        "description": f'The Torn API has raised error code {e.code}: "{e.message}".',
                        "color": 0xC83F49,
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
                        "title": "HTTP Error",
                        "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    faction_balances = faction_balances["donations"]

    if str(user.tid) not in faction_balances:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Error",
                        "description": (
                            f"{user.name} is not in {faction.name}'s donations list according to the Torn API. "
                            f"If you think that this is an error, please report this to the developers of this bot."
                        ),
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if withdrawal_option == 1:
        withdrawal_option_str = "points_balance"
    else:
        withdrawal_option_str = "money_balance"

    if (
        withdrawal_amount != "all"
        and withdrawal_amount > faction_balances[str(user.tid)][withdrawal_option_str]
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Enough",
                        "description": "You do not have enough of the requested currency in the faction vault.",
                        "fields": [
                            {"name": "Amount Requested", "value": withdrawal_amount},
                            {
                                "name": "Amount Available",
                                "value": faction_balances[str(user.tid)][
                                    withdrawal_option_str
                                ],
                            },
                        ],
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif (
        withdrawal_amount == "all"
        and faction_balances[str(user.tid)][withdrawal_option_str] <= 0
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Enough",
                        "description": "You have requested all of your currency, but have zero or a negative vault balance.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    request_id = WithdrawalModel.objects().count()
    send_link = f"https://torn.deek.sh/faction/banking/fulfill/{request_id}"

    if withdrawal_amount != "all":
        message_payload = {
            "content": f'<@&{faction.vault_config["banker"]}>',
            "embeds": [
                {
                    "title": f"Vault Request #{request_id}",
                    "description": f"{user.name} [{user.tid}] is requesting {utils.commas(withdrawal_amount)} "
                    f"in {'points' if withdrawal_option == 1 else 'cash'}"
                    f" from the faction vault. "
                    f"To fulfill this request, enter `?f {request_id}` in this channel.",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
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
                        {"type": 2, "style": 5, "label": "Fulfill", "url": send_link},
                        {
                            "type": 2,
                            "style": 3,
                            "label": "Fulfill Manually",
                            "custom_id": "faction:vault:fulfill",
                        },
                    ],
                }
            ],
        }
    else:
        message_payload = {
            "content": f'<@&{faction.vault_config["banker"]}>',
            "embeds": [
                {
                    "title": f"Vault Request #{request_id}",
                    "description": f"{user.name} [{user.tid}] is requesting "
                    f"{utils.commas(faction_balances[str(user.tid)][withdrawal_option_str])} in "
                    f"{'points' if withdrawal_option == 1 else 'cash'}"
                    f" from the faction vault. "
                    f"To fulfill this request, enter `?f {request_id}` in this channel.",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
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
                        {"type": 2, "style": 5, "label": "Fulfill", "url": send_link},
                        {
                            "type": 2,
                            "style": 3,
                            "label": "Fulfill Manually",
                            "custom_id": "faction:vault:fulfill",
                        },
                    ],
                }
            ],
        }

    message = tasks.discordpost(
        f'channels/{faction.vault_config["banking"]}/messages',
        payload=message_payload,
        dev=True,
    )

    withdrawal = WithdrawalModel(
        wid=request_id,
        amount=withdrawal_amount
        if withdrawal_amount != "all"
        else faction_balances[str(user.tid)][withdrawal_option_str],
        requester=user.tid,
        factiontid=user.factiontid,
        time_requested=utils.now(),
        fulfiller=0,
        time_fulfilled=0,
        withdrawal_message=message["id"],
        wtype=withdrawal_option,
    )
    withdrawal.save()

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": f"Vault Request #{request_id}",
                    "description": "Your vault request has been forwarded to the faction leadership.",
                    "fields": [
                        {
                            "name": "Request Type",
                            "value": "Cash" if withdrawal_option == 0 else "Points",
                        },
                        {"name": "Amount Requested", "value": withdrawal_amount},
                    ],
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }
