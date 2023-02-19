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

import requests

import utils
from models.positionmodel import PositionModel
from models.servermodel import ServerModel
from models.usermodel import UserModel
from tasks import celery_app, discordget, logger


@celery_app.task
def refresh_guilds():
    requests_session = requests.Session()

    try:
        guilds = discordget("users/@me/guilds", session=requests_session)
    except Exception as e:
        logger.exception(e)
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
        except utils.DiscordError as e:
            if e.code == 10007:
                continue
            else:
                logger.exception(e)
                continue
        except Exception as e:
            logger.exception(e)
            continue

        try:
            guild = discordget(f'guilds/{guild["id"]}', session=requests_session)
        except Exception as e:
            logger.exception(e)
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

        logger.info(f"Deleted {guild.name} [{guild.sid}] from database (Reason: not found by Discord API)")
        guild.delete()
