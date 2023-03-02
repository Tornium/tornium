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

import celery
import logging
from mongoengine import QuerySet
import requests

from tornium_commons.errors import DiscordError
from tornium_commons.models import FactionModel, FactionStakeoutModel, NotificationModel, PositionModel, ServerModel, UserModel, UserStakeoutModel

from tasks.api import discordget


@celery.shared_task
def refresh_guilds():
    requests_session = requests.Session()

    try:
        guilds = discordget("users/@me/guilds", session=requests_session)
    except Exception as e:
        logging.getLogger("celery").exception(e)
        return

    guilds_not_updated = [int(server.sid) for server in ServerModel.objects()]

    for guild in guilds:
        if int(guild["id"]) in guilds_not_updated:
            guilds_not_updated.remove(int(guild["id"]))

        guild_db: ServerModel = ServerModel.objects(sid=guild["id"]).first()

        if guild_db is None:
            guild_db = ServerModel(
                sid=guild["id"],
                name=guild["name"],
                admins=[],
                config={"stakeouts": 0, "verify": 0},
                icon=guild["icon"],
                factions=[],
                stakeoutconfig={"category": 0},
                userstakeouts=[],
                factionstakeouts=[],
                assistschannel=0,
                assist_factions=[],
                assist_mod=0,
            )
            guild_db.save()

        try:
            members = discordget(f'guilds/{guild["id"]}/members?limit=1000', session=requests_session)
        except DiscordError as e:
            if e.code == 10007:
                continue
            else:
                logging.getLogger("celery").exception(e)
                continue
        except Exception as e:
            logging.getLogger("celery").exception(e)
            continue

        try:
            guild = discordget(f'guilds/{guild["id"]}', session=requests_session)
        except Exception as e:
            logging.getLogger("celery").exception(e)
            continue

        admins = []
        owner: UserModel = UserModel.objects(discord_id=guild["owner_id"]).first()

        if owner is not None:
            admins.append(owner.tid)

        for member in members:
            user: UserModel = UserModel.objects(discord_id=member["user"]["id"]).first()

            if user is not None and user.key not in (None, ""):
                for role in member["roles"]:
                    for guild_role in guild["roles"]:
                        # Checks if the user has the role and the role has the administrator permission
                        if guild_role["id"] == role and (int(guild_role["permissions"]) & 0x0000000008) == 0x0000000008:
                            admins.append(user.tid)

        admins = list(set(admins))
        guild_db.admins = admins
        guild_db.icon = guild["icon"]
        guild_db.save()

        for factiontid, faction_data in guild_db.faction_verify.items():
            faction_positions_data = faction_data

            if "positions" not in faction_data:
                continue

            for position_uuid, position_data in faction_data["positions"].items():
                position: PositionModel = PositionModel.objects(pid=position_uuid).first()

                if position is None or position.factiontid != int(factiontid):
                    faction_positions_data["positions"].pop(position_uuid)

            guild_db.faction_verify[factiontid] = faction_positions_data

        guild_db.save()

    for deleted_guild in guilds_not_updated:
        guild: ServerModel = ServerModel.objects(sid=deleted_guild).first()

        if guild is None:
            continue

        logging.getLogger("celery").info(f"Deleted {guild.name} [{guild.sid}] from database (Reason: not found by Discord API)")
        guild.delete()


@celery.shared_task
def remove_unknown_channel(channel_id: int):
    channel_id = int(channel_id)

    faction_vault_channel: QuerySet = FactionModel.objects(vaultconfig__banking=channel_id)
    faction_od_channel: QuerySet = FactionModel.objects(chainconfig__odchannel=channel_id)

    notifications: QuerySet = NotificationModel.objects(target=channel_id)

    server_verify_channel: typing.Optional[ServerModel] = ServerModel.objects(verify_log_channel=channel_id).first()
    server_assist_channel: typing.Optional[ServerModel] = ServerModel.objects(assistschannel=channel_id).first()

    faction: FactionModel
    for faction in faction_vault_channel:
        faction.vaultconfig["banking"] = 0
        faction.save()

    faction: FactionModel
    for faction in faction_od_channel:
        faction.chainod["odchannel"] = 0
        faction.save()

    if notifications.count() > 0:
        notifications.delete()

    if server_verify_channel is not None:
        server_verify_channel.verify_log_channel = 0
        server_verify_channel.save()

    if server_assist_channel is not None:
        server_assist_channel.assistschannel = 0
        server_assist_channel.save()

    faction_stakeout: FactionStakeoutModel
    for faction_stakeout in FactionStakeoutModel.objects():
        faction_stakeout_data = faction_stakeout.guilds

        for guild, guild_stakeout in faction_stakeout.guilds.copy().items():
            if guild_stakeout.get("channel") in (None, 0, channel_id):
                faction_stakeout_data.pop(guild, None)

        faction_stakeout.guilds = faction_stakeout_data

        if len(faction_stakeout.guilds) == 0:
            faction_stakeout.delete()
        else:
            faction_stakeout.save()

    user_stakeout: UserStakeoutModel
    for user_stakeout in UserStakeoutModel.objects():
        user_stakeout_data = user_stakeout.guilds

        for guild, guild_stakeout in user_stakeout.guilds.copy().items():
            if guild_stakeout.get("channel") in (None, 0, channel_id):
                user_stakeout_data.pop(guild, None)

        user_stakeout.guilds = user_stakeout_data

        if len(user_stakeout.guilds) == 0:
            user_stakeout.delete()
        else:
            user_stakeout.save()

    server: ServerModel
    for server in ServerModel.objects():
        for faction_id, faction_oc in server.oc_config.copy().items():
            if int(faction_oc["ready"]["channel"]) == channel_id:
                server.oc_config[faction_id]["ready"]["channel"] = 0
            if int(faction_oc["delay"]["channel"]) == channel_id:
                server.oc_config[faction_id]["delay"]["channel"] = 0

        server.save()


@celery.shared_task()
def remove_unknown_role(role_id: int):
    role_id = int(role_id)

    faction_vault_role: QuerySet = FactionModel.objects(vaultconfig__banker=role_id)

    server_verify_roles: typing.Optional[ServerModel] = ServerModel.objects(verified_roles=role_id).first()

    faction: FactionModel
    for faction in faction_vault_role:
        faction.vaultconfig["banker"] = 0
        faction.save()

    server: ServerModel
    for server in server_verify_roles:
        server.verified_roles.remove(role_id)
        server.save()

    server: ServerModel
    for server in ServerModel.objects():
        server_verify = server.faction_verify

        for faction_id, faction_verify in server.faction_verify.copy().items():
            if role_id in faction_verify["roles"]:
                server_verify[faction_id]["roles"].remove(role_id)

        server.faction_verify = server_verify
        server_oc_config = server.oc_config

        for faction_id, faction_oc in server.oc_config.copy().items():
            if str(role_id) in faction_oc["ready"]["roles"]:
                server_oc_config[faction_id]["ready"]["roles"].remove(str(role_id))
            if str(role_id) in faction_oc["delay"]["roles"]:
                server_oc_config[faction_id]["delay"]["roles"].remove(str(role_id))

        server.oc_config = server_oc_config
        server.save()
