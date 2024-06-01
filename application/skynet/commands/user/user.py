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
from tornium_commons.errors import MissingKeyError
from tornium_commons.formatters import find_list
from tornium_commons.models import User
from tornium_commons.skyutils import SKYNET_ERROR


def user_who(interaction, *args, **kwargs):
    user_mention = find_list(interaction["data"].get("options", {}), "name", "member")
    user_tid = find_list(interaction["data"].get("options", {}), "name", "tid")
    force = find_list(interaction["data"].get("options", {}), "name", "force", default=False)

    if user_mention is not None and user_tid is not None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid User Parameter",
                        "description": "You need to select either a Torn user ID/name or a Discord user mention, but not both.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    if not isinstance(force, bool):
        force = bool(force["value"])

    user: typing.Optional[User]
    user_id: typing.Tuple[int, bool]  # User/Discord ID, is Torn ID bool

    if user_mention is None and user_tid is None:
        user = kwargs["invoker"]
    elif user_mention is not None and user_tid is None:
        user = User.select().where(User.discord_id == user_mention["value"]).first()
        user_id = (user_mention["value"], False)
    elif user_mention is None and user_tid is not None:
        user_tid["value"]: str

        if user_tid["value"].isdigit():
            user = User.select().where(User.tid == user_tid["value"]).first()
            user_id = (user_tid["value"], True)
        else:
            try:
                user = User.select().where(User.name == user_tid["value"]).get()
                user_id = (user.tid, True)
            except DoesNotExist:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Invalid User Name",
                                "description": "No user could be found in the database with this name. Please try using their Torn ID instead.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }
    else:
        return {}  # TODO: Add error message

    try:
        if user_id[1]:
            update_user(key=random.choice(kwargs["admin_keys"], tid=user_id[0]), refresh_existing=force)
        else:
            update_user(key=random.choice(kwargs["admin_keys"], discord_id=user_id[0]), refresh_existing=force)
    except (IndexError, MissingKeyError):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Keys",
                        "description": "No API keys were found to be run for this command. Please sign into Tornium or run this command in a server with signed-in admins.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        if user_id[1]:
            user = User.select().where(User.tid == user_id[0]).get()
        else:
            user = User.select().where(User.discord_id == user_id[0]).get()
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Not Found",
                        "description": "The user could not be found in the database. Please try again with force.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    return user.user_embed()

