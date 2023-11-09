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
from tornium_celery.tasks.user import update_user
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.formatters import bs_to_range, commas, find_list
from tornium_commons.models import Stat, User
from tornium_commons.skyutils import SKYNET_ERROR

from skynet.skyutils import get_admin_keys


def stat(interaction, *args, **kwargs):
    user: User = kwargs["invoker"]

    if "options" not in interaction["data"]:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameters",
                        "description": "The parameter passed must be either the Torn ID or a Torn name.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    tid = find_list(interaction["data"]["options"], "name", "tornid")
    name = find_list(interaction["data"]["options"], "name", "name")

    if (tid == -1 and name == -1) or (tid != -1 and name != -1):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameters",
                        "description": "The parameter passed must be either the Torn ID or a Torn name.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    admin_keys = kwargs.get("admin_keys", get_admin_keys(interaction))

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
                "flags": 64,
            },
        }

    target_user: typing.Optional[User] = None

    target: typing.Optional[Stat]
    if tid != -1:
        try:
            target = (
                Stat.select()
                .where(
                    (Stat.tid == tid[1]["value"]) & ((Stat.added_group == 0) | (Stat.added_group == user.faction.tid))
                )
                .order_by(-Stat.time_added)
                .get()
            )
        except DoesNotExist:
            target = None
    elif name != -1:
        try:
            target_user = User.select(User.name, User.tid, User.faction).where(User.name == name[1]["value"]).get()
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Unknown User",
                            "description": "No Torn user could be located in the database with that name.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }

        try:
            target = (
                Stat.select()
                .where(
                    (Stat.tid == target_user.tid) & ((Stat.added_group == 0) | (Stat.added_group == user.faction.tid))
                )
                .order_by(-Stat.time_added)
                .get()
            )
        except DoesNotExist:
            target = None
    else:
        target = None

    if target is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Not Located",
                        "description": "The specified user could not be found with your permissions in the stat "
                        "database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        update_user(random.choice(admin_keys), tid=target.tid, refresh_existing=False)
    except TornError as e:
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
                "flags": 64,
            },
        }
    except NetworkingError as e:
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
                "flags": 64,
            },
        }

    if target_user is None:
        try:
            target_user = User.select(User.name, User.tid, User.faction).get_by_id(target.tid)
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "User Not Located",
                            "description": "The user could not be located in the Tornium database.",
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
                    "title": f"{target_user.name} [{target_user.tid}]",
                    "url": f"https://www.torn.com/profiles.php?XID={target_user.tid}",
                    "fields": [
                        {
                            "name": "Faction",
                            "value": f"{target_user.faction.name if target_user.faction is not None else 'Unknown/No Faction'}",
                        },
                        {
                            "name": "Last Action",
                            "value": f"<t:{target_user.last_action}:R>",
                        },
                        {
                            "name": "Minimum Total Stats",
                            "value": commas(bs_to_range(target.battlescore)[0]),
                            "inline": True,
                        },
                        {
                            "name": "Maximum Total Stats",
                            "value": commas(bs_to_range(target.battlescore)[1]),
                            "inline": True,
                        },
                        {
                            "name": "Estimated Stat Score",
                            "value": commas(round(target.battlescore, 2)),
                            "inline": True,
                        },
                        {
                            "name": "Stat Score Update",
                            "value": f"<t:{target.time_added.timestamp()}:R>",
                            "inline": True,
                        },
                    ],
                }
            ]
        },
    }
