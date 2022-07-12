# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from honeybadger import honeybadger
import requests

from models.servermodel import ServerModel
from models.usermodel import UserModel
from tasks import celery_app, discordget, logger
import utils


@celery_app.task
def refresh_guilds():
    requests_session = requests.Session()

    try:
        guilds = discordget("users/@me/guilds", session=requests_session)
    except Exception as e:
        logger.exception(e)
        honeybadger.notify(e)
        return

    for guild in guilds:
        guild_db: ServerModel = utils.first(ServerModel.objects(sid=guild["id"]))

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
                skynet=False,
            )
            guild_db.save()

        try:
            members = discordget(
                f'guilds/{guild["id"]}/members', session=requests_session
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

        admins = guild_db.admins

        owner: UserModel = utils.first(UserModel.objects(discord_id=guild["owner_id"]))

        if owner is not None and guild["id"] not in owner.servers:
            owner.servers.append(guild["id"])
            owner.servers = list(set(owner.servers))
            owner.save()
        if owner is not None:
            admins.append(owner.tid)

        for member in members:
            user: UserModel = utils.first(
                UserModel.objects(discord_id=member["user"]["id"])
            )

            if user is not None:
                for role in member["roles"]:
                    for guild_role in guild["roles"]:
                        # Checks if the user has the role and the role has the administrator permission
                        if (
                            guild_role["id"] == role
                            and (int(guild_role["permissions"]) & 0x0000000008)
                            == 0x0000000008
                        ):
                            user.servers.append(guild["id"])
                            user.servers = list(set(user.servers))
                            user.save()

                            admins.append(user.tid)
                        else:
                            if guild["id"] in user.servers:
                                user.servers.remove(guild["id"])
                                user.servers = list(set(user.servers))
                                user.save()

                                if user.tid in admins:
                                    admins.remove(user.tid)

        admins = list(set(admins))
        guild_db.admins = admins
        guild_db.save()
