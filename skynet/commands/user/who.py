# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from models.factionmodel import FactionModel
from models.server import Server
from models.usermodel import UserModel
from tasks.user import update_user
import utils


def who(interaction):
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
    admin_keys = []

    for admin in server.admins:
        admin_user: UserModel = UserModel.objects(tid=admin).first()

        if admin_user is None:
            continue
        elif admin_user.key in ("", None):
            continue

        admin_keys.append(admin_user.key)

    if "options" in interaction["data"]:
        member = utils.find_list(interaction["data"]["options"], "name", "member")
        tid = utils.find_list(interaction["data"]["options"], "name", "tid")

        if (member == -1 and tid == -1) or (member != -1 and tid != -1):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Parameters",
                            "description": "The parameter passed must be either the Torn ID or a member mention.",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }

        # TODO: Verify that mentioned user is not a bot

        try:
            user: UserModel
            user, user_data = update_user(
                key=random.choice(admin_keys),
                discordid=member[1]["value"] if member != 1 else tid[1]["value"],
                refresh_existing=True
            )
        except utils.TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Torn API Error #{e.code}",
                            "description": f"The Torn API has responded to the API call with \"{e.message}\".",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }
        except utils.NetworkingError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"HTTP Error Code {e.code}",
                            "description": f"The Torn API has responded to the API call with a networking error... "
                                           f"\"{e.message}\".",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }
        except Exception as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Miscellaneous Exception",
                            "description": f"The Torn API call has resulted with a miscellaneous error.",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }

        if member != -1:
            user: UserModel = UserModel.objects(
                discord_id=member[1]["value"]
            ).first()

            if user is None:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Unknown User",
                                "description": "The mention Discord member could not be located. The user may not be "
                                               "officially verified. Please try using their Torn ID if you know that.",
                                "color": 0xC83F49,
                            }
                        ],
                        "flags": 64,  # Ephemeral
                    }
                }
        else:
            user: UserModel = UserModel.objects(
                tid=tid[1]["value"]
            ).first()

            if user is None:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Unknown User",
                                "description": "The passed Torn ID could not be located.",
                                "color": 0xC83F49,
                            }
                        ],
                        "flags": 64,  # Ephemeral
                    }
                }
    else:
        if "member" in interaction:
            user: UserModel = UserModel.objects(
                discord_id=interaction["member"]["user"]["id"]
            ).first()
        else:
            user: UserModel = UserModel.objects(
                discord_id=interaction["user"]["id"]
            ).first()

        if user is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Unverified Member",
                            "descriptions": "The command invoker is not stored in the database. Please wait for the "
                                            "respective automated task to be run. Or alternatively, you can sign into "
                                            "Tornium. However, please make sure that you are officially verified by "
                                            "Torn; otherwise you'll need to verify on the "
                                            "[official Discord server](https://www.torn.com/discord).",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }

        if user.key in ("", None):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"{user.name} [{user.tid}]",
                            "fields": [
                                {
                                    "name": "Level",
                                    "value": f"Level {user.level}",
                                    "inline": True,
                                },
                                {
                                    "name": "Faction",
                                    "value": f"Faction N/A [{user.factionid}]",
                                    "inline": True
                                },
                            ],
                            "footer": {
                                "text": "User data not refreshed. No available API keys."
                            }
                        }
                    ]
                }
            }

        try:
            user: UserModel
            user, user_data = update_user(
                key=user.key,
                tid=user.tid,
                refresh_existing=True
            )
        except utils.TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Torn API Error #{e.code}",
                            "description": f"The Torn API has responded to the API call with \"{e.message}\".",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }
        except utils.NetworkingError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"HTTP Error Code {e.code}",
                            "description": f"The Torn API has responded to the API call with a networking error... "
                                           f"\"{e.message}\".",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }
        except Exception as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Miscellaneous Exception",
                            "description": f"The Torn API call has resulted with a miscellaneous error.",
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                }
            }

    if user.factionid != 0:
        faction: FactionModel = FactionModel.objects(tid=user.factionid).first()

        if faction is not None:
            faction_str = f"{faction.name} [{faction.tid}]"
        else:
            faction_str = f"N/A [{user.factionid}]"
    else:
        faction_str = "None"

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": f"{user.name} [{user.tid}]",
                    "fields": [
                        {
                            "name": "Level",
                            "value": f"Level {user.level}",
                            "inline": True,
                        },
                        {
                            "name": "Life",
                            "value": f"NYI/NYI",  # TODO: Get current and max life from Torn API
                            "inline": True
                        },
                        {
                            "name": "Faction",
                            "value": f"{faction_str}",
                            "inline": True,
                        },
                        {
                            "name": "Company",
                            "value": "NYI",  # TODO: Get value from Torn API
                            "inline": True
                        },  # TODO: Add other fields from API data
                    ],
                    "color": 0x32CD32,
                }
            ],
            "components": [
                {
                    "type": 1,
                    "components": [  # TODO: Automatically remove links if not applicable
                        {
                            "type": 2,
                            "style": 5,
                            "label": "User",
                            "url": f"https://www.torn.com/profiles.php?XID={user.tid}"
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Attack Link",
                            "url": f"https://www.torn.com/loader.php?sid=attack&user2ID={user.tid}"  # TODO: Update link
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Faction",
                            "url": f"https://www.torn.com/factions.php?step=profile&ID={user.factionid}#/"  # TODO: Update link
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Company",
                            "url": f"https://www.torn.com"  # TODO: Update Link
                        }
                    ]
                }
            ],
            "flags": 64,  # Ephemeral
        }
    }
