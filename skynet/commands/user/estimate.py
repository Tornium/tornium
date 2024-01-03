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
import time
import typing

from tornium_commons.formatters import bs_to_range, commas, find_list
from tornium_commons.models import User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from estimate import estimate_user


def estimate_command(interaction, *args, **kwargs):
    start_time = time.time()

    if "options" in interaction["data"]:
        user_mention = find_list(interaction["data"]["options"], "name", "member")
        user_tid = find_list(interaction["data"]["options"], "name", "tid")
    else:
        user_mention = -1
        user_tid = -1

    if not ((user_mention != -1) ^ (user_tid != -1)):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid User",
                        "description": "Either a Torn user ID/name or a Discord user mention must be provided.",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }

    mentioned_user: typing.Optional[User]
    if user_mention != -1:
        mentioned_user = User.select(User.tid, User.name).where(User.discord_id == user_mention[1]["value"]).first()
    elif user_tid != -1:
        if user_tid[1]["value"].isdigit():
            mentioned_user = User.select(User.tid, User.name).where(User.tid == user_tid[1]["value"]).first()
        else:
            mentioned_user = User.select(User.tid, User.name).where(User.name == user_tid[1]["value"]).first()

    api_key = kwargs["invoker"].key if kwargs["invoker"] is not None else None

    if api_key in (None, ""):
        if len(kwargs["admin_keys"]) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Missing API Key",
                            "description": "An API key is required to perform this interaction. Please sign into Tornium or use this command in a server where an admin is signed in.",
                            "color": SKYNET_ERROR,
                        },
                    ],
                    "flags": 64,
                },
            }

        if len(kwargs["admin_keys"]) == 1:
            api_key = kwargs["admin_keys"][0]
        else:
            api_key = random.choice(kwargs["admin_keys"])

    stat_score, _ = estimate_user(mentioned_user.tid, api_key)
    stat_score = int(stat_score)

    minimum_stats, maximum_stats = bs_to_range(stat_score)

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "User Stat Estimate",
                    "description": f"{mentioned_user.name} [{mentioned_user.tid}] is estimated to have a stat score of {commas(stat_score)}.",
                    "fields": [
                        {"name": "Minimum Total", "value": commas(minimum_stats), "inline": True},
                        {"name": "Maximum Total", "value": commas(maximum_stats), "inline": True},
                    ],
                    "color": SKYNET_GOOD,
                    "footer": {
                        "text": f"Latency: {round(time.time() - start_time, 2)} seconds",
                    },
                }
            ],
            "flags": 64,
        },
    }
