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

import tasks
import tasks.api
import utils
from models.faction import Faction
from models.user import User
from models.usermodel import UserModel
from skynet.skyutils import SKYNET_ERROR, SKYNET_GOOD, get_admin_keys, get_faction_keys, invoker_exists


@invoker_exists
def balance(interaction, *args, **kwargs):
    print(interaction)

    user: UserModel = kwargs["invoker"]
    member = -1

    if "options" in interaction["data"]:
        member = utils.find_list(interaction["data"]["options"], "name", "member")

        if member != -1:
            member_db: UserModel = UserModel.objects(discord_id=int(member[1]["value"])).first()

            if member_db is not None and member_db.tid:
                user = member_db
            else:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Verification Incomplete",
                                "description": "This member could not be located in the database. Run `/verify` on the "
                                "specified member. Inline verification is under construction currently.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,  # Ephemeral
                    },
                }

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

    if user.factiontid != kwargs["invoker"].factionid or (not kwargs["invoker"].factionaa and member != -1):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "To check other members' balances, you must be an AA member of their faction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    faction = Faction(user.factiontid)

    if faction.config.get("vault") in [0, None]:
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

    aa_keys = get_faction_keys(interaction, faction)

    if len(aa_keys) == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Keys",
                        "description": "No AA API keys were found to be run for this command. Please sign into "
                        "Tornium or ask a faction AA member to sign into Tornium.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    try:
        faction_balances = tasks.api.tornget("faction/?selections=donations", random.choice(aa_keys))
    except utils.TornError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Torn API Error",
                        "description": f'The Torn API has raised error code {e.code}: "{e.message}".',
                        "color": SKYNET_ERROR,
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
                        "color": SKYNET_ERROR,
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
                        "color": SKYNET_ERROR,
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
                    "title": f"Vault Balance of "
                    f"{user.name if user.name != '' else interaction['member']['user']['username']}",
                    "fields": [
                        {
                            "name": "Cash Balance",
                            "value": f"${utils.commas(faction_balances[str(user.tid)]['money_balance'])}",
                        },
                        {
                            "name": "Points Balance",
                            "value": f"{utils.commas(faction_balances[str(user.tid)]['points_balance'])}",
                        },
                    ],
                    "color": SKYNET_GOOD,
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
                            "url": "https://www.torn.com/factions.php?step=your#/tab=armoury",
                        }
                    ],
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }
