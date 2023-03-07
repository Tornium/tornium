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

import random

from tornium_celery.tasks.user import update_user
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.formatters import find_list
from tornium_commons.models import FactionModel, UserModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from skynet.skyutils import get_admin_keys


def who(interaction):
    if "options" in interaction["data"]:
        member = find_list(interaction["data"]["options"], "name", "member")
        tid = find_list(interaction["data"]["options"], "name", "tid")

        if (member == -1 and tid == -1) or (member != -1 and tid != -1):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Parameters",
                            "description": "The parameter passed must be either the Torn ID or a member mention.",
                            "color": SKYNET_ERROR,
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
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        # TODO: Verify that mentioned user is not a bot

        try:
            update_user(
                key=random.choice(admin_keys),
                discordid=member[1]["value"] if member != 1 else tid[1]["value"],
                refresh_existing=True,
            ).get()
        except TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Torn API Error #{e.code}",
                            "description": f'The Torn API has responded to the API call with "{e.message}".',
                            "color": SKYNET_ERROR,
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
                            "title": f"HTTP Error Code {e.code}",
                            "description": f"The Torn API has responded to the API call with a networking error... "
                            f'"{e.message}".',
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
        except Exception:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Miscellaneous Exception",
                            "description": "The Torn API call has resulted with a miscellaneous error.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        if member != -1:
            user: UserModel = UserModel.objects(discord_id=member[1]["value"]).first()

            if user is None:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Unknown User",
                                "description": "The mention Discord member could not be located. The user may not be "
                                "officially verified. Please try using their Torn ID if you know that.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,  # Ephemeral
                    },
                }
        else:
            user: UserModel = UserModel.objects(tid=tid[1]["value"]).first()

            if user is None:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Unknown User",
                                "description": "The passed Torn ID could not be located.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,  # Ephemeral
                    },
                }
    else:
        if "member" in interaction:
            user: UserModel = UserModel.objects(discord_id=interaction["member"]["user"]["id"]).first()
        else:
            user: UserModel = UserModel.objects(discord_id=interaction["user"]["id"]).first()

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
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
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
                                    "inline": True,
                                },
                            ],
                            "footer": {"text": "User data not refreshed. No available API keys."},
                        }
                    ]
                },
            }

        try:
            update_user(key=user.key, tid=user.tid, refresh_existing=True).get()
        except TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Torn API Error #{e.code}",
                            "description": f'The Torn API has responded to the API call with "{e.message}".',
                            "color": SKYNET_ERROR,
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
                            "title": f"HTTP Error Code {e.code}",
                            "description": f"The Torn API has responded to the API call with a networking error... "
                            f'"{e.message}".',
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
        except Exception:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Miscellaneous Exception",
                            "description": "The Torn API call has resulted with a miscellaneous error.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
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
                            "value": "NYI/NYI",  # TODO: Get current and max life from Torn API
                            "inline": True,
                        },
                        {
                            "name": "Faction",
                            "value": f"{faction_str}",
                            "inline": True,
                        },
                        {
                            "name": "Company",
                            "value": "NYI",  # TODO: Get value from Torn API
                            "inline": True,
                        },  # TODO: Add other fields from API data
                    ],
                    "color": SKYNET_GOOD,
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
                            "url": f"https://www.torn.com/profiles.php?XID={user.tid}",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Attack Link",
                            "url": f"https://www.torn.com/loader.php?sid=attack&user2ID={user.tid}",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Faction",
                            "url": f"https://www.torn.com/factions.php?step=profile&ID={user.factionid}#/",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Company",
                            "url": "https://www.torn.com",  # TODO: Update Link
                        },
                    ],
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }
