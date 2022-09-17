# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>
import random

from models.usermodel import UserModel
from skynet.skyutils import get_admin_keys
from tasks.user import update_user
import utils


def verify(interaction):
    print(interaction)

    if "options" in interaction:
        member = utils.find_list(interaction["data"]["options"], "name", "member")

        if member != -1:
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
                },
            }

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
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        try:
            user: UserModel
            user, user_data = update_user(
                key=random.choice(admin_keys),
                discordid=member[1]["value"],
                refresh_existing=True,
            )
        except utils.TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Torn API Error #{e.code}",
                            "description": f'The Torn API has responded to the API call with "{e.message}".',
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
                            "title": f"HTTP Error Code {e.code}",
                            "description": f"The Torn API has responded to the API call with a networking error... "
                            f'"{e.message}".',
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
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
                },
            }
    else:
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
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        try:
            if "member" in interaction:
                user: UserModel
                user, user_data = update_user(
                    key=random.choice(admin_keys),
                    discordid=interaction["member"]["user"]["id"],
                    refresh_existing=True,
                )
            else:
                user: UserModel
                user, user_date = update_user(
                    key=random.choice(admin_keys),
                    discordid=interaction["user"]["id"],
                    refresh_existing=True
                )
        except utils.TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Torn API Error #{e.code}",
                            "description": f'The Torn API has responded to the API call with "{e.message}".',
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
                            "title": f"HTTP Error Code {e.code}",
                            "description": f"The Torn API has responded to the API call with a networking error... "
                            f'"{e.message}".',
                            "color": 0xC83F49,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
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
                },
            }

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Verification Successful",
                    "description":
                        f"""Torn: [{user.name} [{user.tid}]](https://www.torn.com/profiles.php?XID={user.tid})
                        Discord: <@{user.discord_id}>
                        """
                }
            ]
        }
    }
