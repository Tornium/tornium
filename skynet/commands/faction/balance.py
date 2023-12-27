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
import typing

from peewee import DoesNotExist
from tornium_celery.tasks.api import tornget
from tornium_commons.formatters import commas, find_list
from tornium_commons.models import User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from skynet.skyutils import get_faction_keys


def balance(interaction, *args, **kwargs):
    user: typing.Optional[User] = kwargs["invoker"]
    member = -1

    if "options" in interaction["data"]:
        member = find_list(interaction["data"]["options"], "name", "member")

        if member != -1:
            try:
                user = User.select().where(User.discord_id == int(member[1]["value"])).get()
            except DoesNotExist:
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
                        "flags": 64,
                    },
                }

    elif user is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Not Found",
                        "description": "The mentioned user or the invoker could not be found in the database. Please "
                        "try verifying or signing into Tornium.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Faction Not Found",
                        "description": "The mentioned user or the invoker is not currently in a faction in the "
                        "database. Please try force verifying if you are in a faction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction.tid != kwargs["invoker"].faction.tid or (not kwargs["invoker"].faction_aa and member != -1):
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
                "flags": 64,
            },
        }

    aa_keys = get_faction_keys(interaction, user.faction)

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
                "flags": 64,
            },
        }

    faction_balances = tornget("faction/?selections=donations", random.choice(aa_keys))["donations"]

    if str(user.tid) not in faction_balances:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Error",
                        "description": (
                            f"{user.name} is not in {user.faction.name}'s donations list according to the Torn API. "
                            f"If you think that this is an error, please report this to the developers of this bot."
                        ),
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
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
                            "value": f"${commas(faction_balances[str(user.tid)]['money_balance'])}",
                        },
                        {
                            "name": "Points Balance",
                            "value": f"{commas(faction_balances[str(user.tid)]['points_balance'])}",
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
            "flags": 64,
        },
    }
