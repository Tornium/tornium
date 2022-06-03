# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import random

from models.faction import Faction
from models.server import Server
from models.user import User
from models.usermodel import UserModel
from models.withdrawalmodel import WithdrawalModel
import tasks
import utils


def fulfill_command(interaction):
    print(interaction)

    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Allowed",
                        "description": "This command can not be run in a DM (for now).",
                        "color": 0xC83F49
                    }
                ],
                "flags": 64  # Ephemeral
            }
        }
    server = Server(interaction["guild_id"])

    if "member" in interaction:
        user: UserModel = utils.first(
            UserModel.objects(discord_id=interaction["member"]["user"]["id"])
        )
    else:
        user: UserModel = utils.first(
            UserModel.objects(discord_id=interaction["user"]["id"])
        )
    
    if "options" not in interaction["data"]:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Withdrawal Request Failed",
                        "description": "No options were passed with the "
                        "request. The withdrawal amount option is required.",
                        "color": 0xC83F49
                    }
                ],
                "flags": 64  # Ephemeral
            }
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
        admin: UserModel = utils.first(UserModel.objects(tid=admin_id))

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
                    "flags": 64  # Ephemeral
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
                    "flags": 64  # Ephemeral
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
                    "flags": 64  # Ephemeral
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
                "flags": 64  # Ephemeral
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
                        "flags": 64  # Ephemeral
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
                "flags": 64  # Ephemeral
            },
        }
    
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
    
    faction = Faction(user.factiontid)

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

    withdrawal_id = utils.find_list(interaction["data"]["options"], "name", "id")

    if withdrawal_id == -1:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameters Passed",
                        "description": "No withdrawal ID was passed, but is required.",
                        "color": 0xC83F49
                    }
                ],
                "flags": 64  # Ephemeral
            }
        }
    
    withdrawal_id = withdrawal_id[1]["value"]

    if type(withdrawal_id) == str and not withdrawal_id.isdigit():
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameter Value",
                        "description": "An illegal withdrawal ID type was passed. The withdrawal ID must be an integer.",
                        "color": 0xC83F49
                    }
                ],
                "flags": 64  # Ephemeral
            }
        }

    withdrawal: WithdrawalModel = utils.first(WithdrawalModel.objects(wid=int(withdrawal_id)))

    if withdrawal is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Does not Exist",
                        "description": f"Vault Request #{withdrawal_id} does not currently exist.",
                        "color": 0xC83F49
                    }
                ],
                "flags": 64  # Ephemeral
            }
        }
    elif withdrawal.fulfiller != 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Request Already Fulfilled",
                        "description": f"Vault Request #{withdrawal_id} has already been fulfilled by "
                            f"{User(withdrawal.fulfiller).name} at {utils.torn_timestamp(withdrawal.time_fulfilled)}.",
                        "color": 0xC83F49
                    }
                ],
                "flags": 64  # Ephemeral
            }
        }
    
    try:
        tasks.discordpatch(
            f"channels/{faction.vault_config['banking']}/messages{withdrawal.withdrawal_message}",
            {
                "embeds": [
                    {
                        "title": f"Vault Request #{withdrawal_id}",
                        "description": f"This request has been fulfilled by {user.name} [{user.tid}].",
                        "fields": [
                            {
                                "name": "Original Request Amount",
                                "value": utils.commas(withdrawal.amount)
                            },
                            {
                                "name": "Original Request Type",
                                "value": "Points" if withdrawal.wtype == 1 else "Cash"
                            }
                        ],
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
                                "url": "https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user"
                            },
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Fulfill",
                                "url": f"https://torn.deek.sh/faction/banking/fulfill/{withdrawal_id}"
                            }
                        ]
                    }
                ]
            },
            dev=True
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
                            {
                                "name": "Error Code",
                                "value": e.code
                            },
                            {
                                "name": "Error Message",
                                "value": e.message
                            }
                        ]
                    }
                ]
            }
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
                            {
                                "name": "HTTP Error Code",
                                "value": e.code
                            },
                            {
                                "name": "HTTP Error Message",
                                "value": e.message
                            }
                        ]
                    }
                ]
            }
        }
    
    withdrawal.fulfiller = user.tid
    withdrawal.time_fulfilled = utils.now()
    withdrawal.save()

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": f"Banking Request {withdrawal_id} Fulfilled",
                    "description": "You have fulfilled the banking request.",
                    "color": 0x32CD32
                }
            ],
            "flags": 64  # Ephemeral
        }
    }
