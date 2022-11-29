# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from honeybadger import honeybadger
import requests

from models.positionmodel import PositionModel
from models.servermodel import ServerModel
from models.usermodel import UserModel
from tasks import celery_app, discordget, logger
import utils


@celery_app.task
def refresh_guilds():
    requests_session = requests.Session()

    try:
        guilds = discordget("users/@me/guilds", session=requests_session, dev=True)
    except Exception as e:
        logger.exception(e)
        honeybadger.notify(e)
        return

    for guild in guilds:
        guild_db: ServerModel = ServerModel.objects(sid=guild["id"]).first()

        if guild_db is None:
            guild_db = ServerModel(
                sid=guild["id"],
                name=guild["name"],
                admins=[],
                prefix="?",
                config={"stakeouts": 0, "assists": 0},
                factions=[],
                stakeoutconfig={"category": 0},
                userstakeouts=[],
                factionstakeouts=[],
                assistschannel=0,
                assist_factions=[],
                assist_mod=0,
                skynet=True,
            )
            guild_db.save()
        elif not guild_db.skynet:
            guild_db.skynet = True
            guild_db.save()

        try:
            members = discordget(
                f'guilds/{guild["id"]}/members?limit=1000', session=requests_session
            )
        except utils.DiscordError as e:
            if e.code == 10007:
                continue
            else:
                logger.exception(e)
                honeybadger.notify(e)
                continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        try:
            guild = discordget(f'guilds/{guild["id"]}', session=requests_session)
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
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
                        if (
                            guild_role["id"] == role
                            and (int(guild_role["permissions"]) & 0x0000000008)
                            == 0x0000000008
                        ):
                            admins.append(user.tid)

        admins = list(set(admins))
        guild_db.admins = admins
        guild_db.save()

        for factiontid, faction_data in guild_db.faction_verify.items():
            faction_positions_data = faction_data

            if "positions" not in faction_data:
                continue

            for position_uuid, position_data in faction_data["positions"].items():
                position: PositionModel = PositionModel.objects(
                    pid=position_uuid
                ).first()

                if position is None or position.factiontid != int(factiontid):
                    faction_positions_data["positions"].pop(position_uuid)

            guild_db.faction_verify[factiontid] = faction_positions_data

        guild_db.save()
