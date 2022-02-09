# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

from honeybadger import honeybadger
import requests

from models.usermodel import UserModel
from tasks import celery_app, discordget, logger
import utils


@celery_app.task
def refresh_guilds():
    requests_session = requests.Session()

    try:
        guilds = discordget('users/@me/guilds', session=requests_session)
    except Exception as e:
        logger.exception(e)
        honeybadger.notify(e)
        return
    
    for guild in guilds:
        try:
            members = discordget(f'guilds/{guild["id"]}/members', session=requests_session)
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

        owner: UserModel = utils.first(UserModel.objects(discord_id=guild['owner_id']))

        if owner is not None and guild['id'] not in owner.servers:
            owner.servers.append(guild['id'])
            owner.servers = list(set(owner.servers))
            owner.save()
        
        for member in members:
            user: UserModel = utils.first(UserModel.objects(discord_id=member['user']['id']))

            if user is not None:
                for role in member['roles']:
                    for guild_role in guild['roles']:
                        # Checks if the user has the role and the role has the administrator permission
                        if guild_role['id'] == role and (int(guild_role['permissions']) & 0x0000000008) == 0x0000000008:
                            user.servers.append(guild['id'])
                            user.servers = list(set(user.servers))
                            user.save()
                        else:
                            if guild['id'] in user.servers:
                                user.servers.remove(guild['id'])
                                user.servers = list(set(user.servers))
                                user.save()
