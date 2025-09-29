# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from tornium_commons import rds, with_db_connection

import celery


@celery.shared_task(
    name="tasks.misc.send_dm",
    routing_key="default.send_dm",
    queue="default",
    time_limit=5,
)
@with_db_connection
def send_dm(discord_id: int, payload: dict):
    from .api import discordpost

    try:
        channel_id = int(rds().get(f"tornium:discord:dm:{discord_id}"))
    except TypeError:
        dm_channel = discordpost(
            "users/@me/channels",
            payload={
                "recipient_id": discord_id,
            },
        )

        channel_id = dm_channel["id"]
        rds().set(f"tornium:discord:dm:{discord_id}", channel_id, nx=True, ex=86400)

    return discordpost.delay(endpoint=f"channels/{channel_id}/messages", payload=payload)
