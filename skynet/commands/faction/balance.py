# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from models.faction import Faction
from models.server import Server
from models.user import User
from models.usermodel import UserModel
import redisdb
import tasks
import utils

# Red: C83F49
# Lime: 32CD32
# Blue: 7DF9FF


def balance(interaction):
    server = Server(interaction["guild_id"]) if "guild_id" in interaction else None
    if "member" in interaction:
        user: UserModel = utils.first(UserModel.objects(discord_id=interaction["member"]["user"]["id"]))
    else:
        user: UserModel = utils.first(UserModel.objects(discord_id=interaction["user"]["id"]))

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
                            "color": 0xC83F49
                        }
                    ]
                }
            }
        elif len(server.admins) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No Admins",
                            "description": "There are no admins currently signed into Tornium.",
                            "color": 0xC83F49
                        }
                    ]
                }
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
                            "footer": {
                                "text": f"Unknown Admin ID: {admin_id}"
                            }
                        }
                    ]
                }
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
                            "footer": {
                                "text": f"Borked Admin ID: {admin_id}"
                            }
                        }
                    ]
                }
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
                            "description": f"The Torn API has raised error code {e.code}: \"{e.message}\".",
                            "color": 0xC83F49
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
                            "title": "HTTP Error",
                            "description": f"The Torn API has returned an HTTP error {e.code}: \"{e.message}\".",
                            "color": 0xC83F49
                        }
                    ]
                }
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
                            "color": 0xC83F49
                        }
                    ]
                }
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
                        "color": 0xC83F49
                    }
                ]
            }
        }
    
    user: User = User(user.tid)
    user.refresh(key=User(random.choice(server.admins)).key)

    if user.factiontid == 0:
        user.refresh(key=User(random.choice(server.admins)).key, force=True)

        if user.factiontid == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Faction ID Error",
                            "description": f"The faction ID of {interaction['message']['user']['username']} is not set "
                                           f"regardless of a force refresh.",
                            "color": 0xC83F49
                        }
                    ]
                }
            }
        
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
                        "color": 0xC83F49
                    }
                ]
            }
        }
    
    if faction.config.get("vault") in [0, None]:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The server needs to be added to {faction.name}'s bot configration and to the "
                                       f"server. Please contact the server administrators to do this via "
                                       f"[the dashboard](https://torn.deek.sh).",
                        "color": 0xC83F49
                    }
                ]
            }
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
                        "description": f"The Torn API has raised error code {e.code}: \"{e.message}\".",
                        "color": 0xC83F49
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
                        "title": "HTTP Error",
                        "description": f"The Torn API has returned an HTTP error {e.code}: \"{e.message}\".",
                        "color": 0xC83F49
                    }
                ]
            }
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
                        "color": 0xC83F49
                    }
                ]
            }
        }
        
    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": f"Vault Balance of {user.name if user.name != '' else interaction['member']['user']['username']}",
                    "fields": [
                        {
                            "name": "Cash Balance",
                            "value": f"${utils.commas(faction_balances[str(user.tid)]['money_balance'])}"
                        },
                        {
                            "name": "Points Balance",
                            "value": f"{utils.commas(faction_balances[str(user.tid)]['points_balance'])}"
                        }
                    ]
                }
            ]
        }
    }
