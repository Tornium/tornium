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

import logging
import time
import typing

from peewee import DoesNotExist
from tornium_commons import with_db_connection
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.models import (
    FactionPosition,
    Server,
    ServerAttackConfig,
    ServerNotificationsConfig,
    User,
)

import celery
from celery.utils.log import get_task_logger

from .api import discordget

logger: logging.Logger = get_task_logger("celery_app")


def refresh_guild(guild: dict):
    admins: typing.Set[int] = set()

    try:
        admins.add(User.select(User.tid).where(User.discord_id == guild["owner_id"]).get().tid)
    except DoesNotExist:
        pass

    members = None
    largest_member_id = 0
    while members is None or len(members) >= 1000:
        if members is None:
            members = discordget(f'guilds/{guild["id"]}/members?limit=1000')
        else:
            members = discordget(f"guilds/{guild['id']}/members?limit=1000&after={largest_member_id}")

        discord_admins: typing.Set[int] = set()

        # TODO: Skip bots
        for member in members:
            largest_member_id = max(largest_member_id, int(member["user"]["id"]))

            for guild_role in guild["roles"]:
                # Checks if the user has the role and the role has the administrator permission
                if (
                    guild_role["id"] in member["roles"]
                    and (int(guild_role["permissions"]) & 0x0000000008) == 0x0000000008
                ):
                    try:
                        discord_admins.add(int(member["user"]["id"]))
                    except DoesNotExist:
                        pass

                    break

        admins.update(set(u.tid for u in User.select(User.tid).where(User.discord_id << discord_admins)))

    Server.update(admins=list(set(admins))).where(Server.sid == guild["id"]).execute()

    try:
        guild_db: Server = Server.select().where(Server.sid == guild["id"]).get()

        for faction_tid, faction_data in guild_db.faction_verify.items():
            if "positions" not in faction_data:
                continue

            positions_to_delete = []

            for position_uuid, position_data in faction_data["positions"].items():
                try:
                    position: FactionPosition = (
                        FactionPosition.select(FactionPosition.faction_id)
                        .where(FactionPosition.pid == position_uuid)
                        .get()
                    )
                except DoesNotExist:
                    positions_to_delete.append(position_uuid)
                    continue

                if position.faction_id != int(faction_tid):
                    positions_to_delete.append(position_uuid)

            for position_uuid in positions_to_delete:
                guild_db.faction_verify[faction_tid]["positions"].pop(position_uuid)

        guild_db.save()
    except Exception as e:
        logger.exception(e)


@celery.shared_task(
    name="tasks.guild.refresh_guilds",
    routing_key="default.refresh_guilds",
    queue="default",
    time_limit=3000,
)
@with_db_connection
def refresh_guilds():
    # Largest guild ID and guild count used for pagination if the number of servers
    # is greater than 200 where the API call limits the returned results
    largest_guild_id = None
    guild_count = None

    # Set of guild IDs that no longer have the bot in the server
    guilds_not_updated = set(server.sid for server in Server.select(Server.sid))

    while guild_count is None or guild_count >= 200:
        guild_count = 0

        if largest_guild_id is None:
            guilds = discordget("users/@me/guilds")
        else:
            guilds = discordget(f"users/@me/guilds?after={largest_guild_id}")

        for guild in guilds:
            guild_count += 1

            if largest_guild_id is None or int(guild["id"]) > largest_guild_id:
                largest_guild_id = int(guild["id"])

            try:
                guilds_not_updated.remove(int(guild["id"]))
            except KeyError:
                pass

            Server.insert(
                sid=guild["id"],
                name=guild["name"],
                icon=guild["icon"],
            ).on_conflict(
                conflict_target=[Server.sid],
                preserve=[Server.name, Server.icon],
            ).execute()

            time.sleep(0.5)

            try:
                refresh_guild(discordget(f"guilds/{guild['id']}"))
            except (DiscordError, NetworkingError, celery.exceptions.Retry):
                continue

    # We want to set the IDs to null to prevent a foreign key violation when deleting the server_attack_config and server_notification_config
    Server.update(notifications_config_id=None).where(Server.sid << guilds_not_updated).execute()

    for deleted_guild in guilds_not_updated:
        # Delete certain rows that rely upon the server for the primary key
        try:
            ServerAttackConfig.delete().where(ServerAttackConfig.server == deleted_guild).execute()
            ServerNotificationsConfig.delete().where(ServerNotificationsConfig.server == deleted_guild).execute()
            Server.delete().where(Server.sid == deleted_guild).execute()
        except (DoesNotExist, AttributeError):
            pass
