# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from bot import botutils
from models.faction import Faction
from models.server import Server
from models.user import User
from models.usermodel import UserModel
import redisdb
import tasks
import utils


def transfer(interaction):
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
    transfer_option = utils.find_list(interaction["data"]["options"], "name", "option")

    if transfer_option == -1:
        transfer_option = 0
    elif transfer_option[1]["value"] == "Cash":
        transfer_option = 0
    elif transfer_option[1]["value"] == "Points":
        transfer_option = 1
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Transfer Request Failed",
                        "description": "An incorrect transfer type was passed.",
                        "color": 0xC83F49,
                        "footer": {
                            "text": f"Inputted transfer type: {transfer_option[1]['value']}"
                        },
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    recipient_data = utils.find_list(
        interaction["data"]["options"], "name", "recipient"
    )

    if recipient_data == -1:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Transfer Request Failed",
                        "description": "No recipient was passed to the transfer request.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif recipient_data[1]["value"].isdigit():
        recipient: UserModel = UserModel.objects(
            discord_id=int(recipient_data[1]["value"])
        ).first()
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Transfer Request Failed",
                        "description": "Illegal recipient passed.",
                        "color": 0xC83F49,
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
                f"user/{interaction['member']['user']['id']}?selections=", admin.key
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
            admin=False,
            key="",
            keyaccess=False,
            battlescore=0,
            battlescore_update=0,
            discord_id=user_data["discord"]["discordID"]
            if user_data["discord"]["discordID"] != ""
            else 0,
            servers=[],
            factionid=user_data["faction"]["faction_id"],
            factionaa=False,
            recruiter=False,
            recruiter_code="",
            recruiter_mail_update=0,
            chain_hits=0,
            status=user_data["last_action"]["status"],
            last_action=user_data["last_action"]["timestamp"],
            pro=False,
            pro_expiration=0,
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

    if recipient is None:
        if server is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Error",
                            "description": "Your recipient could not be located in Tornium's databases. Please run this "
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
                f"user/{recipient_data[1]['value']}?selections=", admin.key
            )
        except utils.TornError as e:
            if e.code == 6:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Un-Verified User",
                                "description": "The user mentioned is not a verified Torn user.",
                                "color": 0xC83F49,
                            }
                        ],
                        "flags": 64,  # Ephemeral
                    },
                }

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

        recipient = UserModel(
            tid=user_data["player_id"],
            name=user_data["name"],
            level=user_data["level"],
            last_refresh=utils.now(),
            admin=False,
            key="",
            keyaccess=False,
            battlescore=0,
            battlescore_update=0,
            discord_id=user_data["discord"]["discordID"]
            if user_data["discord"]["discordID"] != ""
            else 0,
            servers=[],
            factionid=user_data["faction"]["faction_id"],
            factionaa=False,
            recruiter=False,
            recruiter_code="",
            recruiter_mail_update=0,
            chain_hits=0,
            status=user_data["last_action"]["status"],
            last_action=user_data["last_action"]["timestamp"],
            pro=False,
            pro_expiration=0,
        )
        recipient.save()

        if recipient.discord_id == 0:
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
    elif recipient.tid == 0:
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
        recipient: User = User(recipient.tid)
        if server is None:
            recipient.refresh()
        else:
            recipient.refresh(key=User(random.choice(server.admins)).key)

        if recipient.factiontid == 0:
            if server is None:
                recipient.refresh(force=True)
            else:
                recipient.refresh(
                    key=User(random.choice(server.admins)).key, force=True
                )

            if recipient.factiontid == 0:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Faction ID Error",
                                "description": f"The faction ID of the recipient is not set regardless of a force refresh.",
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

    if recipient.tid == user.tid:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Transfer Request",
                        "description": "The recipient of the transfer request is the same as the invoker.",
                        "color": 0xC83F49,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif recipient.factiontid != user.factiontid:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Transfer Request",
                        "description": "The recipient of the transfer request is not in the same faction as the invoker.",
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

    transfer_amount = utils.find_list(interaction["data"]["options"], "name", "amount")

    if transfer_amount == -1:
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

    transfer_amount = transfer_amount[1]["value"]

    if type(transfer_amount) == str:
        if transfer_amount.lower() == "all":
            transfer_amount = "all"
        else:
            transfer_amount = botutils.text_to_num(transfer_amount)

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

    if transfer_option == 1:
        transfer_option_str = "points_balance"
    else:
        transfer_option_str = "money_balance"

    if (
        transfer_amount != "all"
        and transfer_amount > faction_balances[str(user.tid)][transfer_option_str]
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Enough",
                        "description": "You do not have enough of the requested currency in the faction vault.",
                        "fields": [
                            {"name": "Amount Requested", "value": transfer_amount},
                            {
                                "name": "Amount Available",
                                "value": faction_balances[str(user.tid)][
                                    transfer_option_str
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
        transfer_amount == "all"
        and faction_balances[str(user.tid)][transfer_option_str] <= 0
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
