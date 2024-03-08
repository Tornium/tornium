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

import typing

from tornium_commons.formatters import commas, find_list
from tornium_commons.models import Stat
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from skynet.skyutils import get_admin_keys


def chain(interaction, *args, **kwargs):
    if "options" in interaction["data"]:
        length = find_list(interaction["data"]["options"], "name", "length")
        difficulty = find_list(interaction["data"]["options"], "name", "difficulty")
        sort = find_list(interaction["data"]["options"], "name", "sort")
    else:
        length = None
        difficulty = None
        sort = None

    length: int
    difficulty: int
    sort: typing.Literal["timestamp", "random", "respect"]

    if length is None:
        length = 9
    else:
        length = length["value"]

    if difficulty is None:
        difficulty = 2
    else:
        difficulty = difficulty["value"]

    if sort is None:
        sort = "timestamp"
    else:
        sort = sort["value"]

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
    elif kwargs["invoker"].battlescore == 0 or kwargs["invoker"].battlescore is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Stats Missing",
                        "description": "The user's battle stats could not be located in the database. Please sign into "
                        "Tornium.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    try:
        chain_list = Stat.generate_chain_list(
            sort=sort,
            difficulty=difficulty,
            limit=length,
            invoker=kwargs["invoker"],
        )
    except ValueError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Parameter",
                        "description": "An inputted paramter to this command may be invalid.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    embed = {
        "title": "Generated Chain List",
        "description": "Depending on the age of the data and the activity of the target, the targets may no longer be accurate. Be sure to double check before attacking.",
        "fields": [],
        "color": SKYNET_GOOD,
        "footer": {"text": ""},
    }
    for stat_entry in chain_list:
        embed["fields"].append(
            {
                "name": f"{stat_entry['user']['name']} [{stat_entry['user']['tid']}]",
                "value": f"Stat Score: {commas(stat_entry['battlescore'])}\nRespect: {stat_entry['respect']}\nLast Update: <t:{int(stat_entry['timeadded'])}:R>\nFaction: {stat_entry['user']['faction']['name']}",
                "inline": True,
            }
        )

    return {
        "type": 4,
        "data": {
            "embeds": [embed],
            "flags": 64,
        },
    }
