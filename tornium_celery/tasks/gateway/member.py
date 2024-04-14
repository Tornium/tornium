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

import datetime
import random
import typing

import celery
from celery.utils.log import get_task_logger
from peewee import DoesNotExist
from tornium_commons import rds
from tornium_commons.formatters import commas, torn_timestamp
from tornium_commons.models import Item, Notification, Server, User
from tornium_commons.skyutils import SKYNET_INFO

from ..api import tornget
from ..guild import verify_member_sub
from ..misc import send_dm

logger = get_task_logger("celery_app")


@celery.shared_task(
    name="tasks.gateway.on_member_join",
    routing_key="quick.gateway.on_member_join",
    queue="quick",
    time_limit=15,
)
def on_member_join(guild_id: int, discord_id: int, user_nick: str):
    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
    except DoesNotExist:
        return

    if not guild.verify_enabled:
        return
    elif guild.verify_template == "" and len(guild.verified_roles) == 0 and len(guild.faction_verify) == 0:
        return
    elif not guild.gateway_verify_enabled:
        return
    elif len(guild.admins) == 0:
        return

    admin_keys: typing.List[str] = []

    admin: int
    for admin in guild.admins:
        try:
            admin_keys.append(User.select(User.tid).where(User.tid == admin).get().key)
        except DoesNotExist:
            continue

    if len(admin_keys) == 0:
        return

    tornget.signature(
        kwargs={
            "endpoint": f"user/{discord_id}?selections=",
            "key": random.choice(admin_keys),
        }
    ).apply_async(
        link=verify_member_sub.signature(
            kwargs={
                "member": {
                    "id": discord_id,
                    "name": user_nick,
                    "icon": None,
                    "roles": [],
                },
                "log_channel": -1 if guild.verify_log_channel == 0 else guild.verify_log_channel,
                "guild_id": guild.sid,
                "gateway": True,
            },
            immutable=True,
        ),
    )
