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

import math

from honeybadger import honeybadger
import requests

from models.usermodel import UserModel
from tasks import celery_app, logger, tornget
import utils


@celery_app.task
def refresh_users():
    reqeusts_session = requests.Session()

    user: UserModel
    for user in UserModel.objects(key__ne=''):
        if user.key == '':
            continue

        try:
            user_data = tornget(f'user/?selections=profile,battlestats,discord', user.key, session=reqeusts_session)
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        user.factionid = user_data['faction']['faction_id']
        user.name = user_data['name']
        user.last_refresh = utils.now()
        user.status = user_data['last_action']['status']
        user.last_action = user_data['last_action']['timestamp']
        user.level = user_data['level']
        user.discord_id = user_data['discord']['discordID'] if user_data['discord']['discordID'] != '' else 0
        user.strength = user_data['strength']
        user.defense = user_data['defense']
        user.speed = user_data['speed']
        user.dexterity = user_data['dexterity']

        battlescore = math.sqrt(user_data['strength']) + math.sqrt(user_data['defense']) + \
                      math.sqrt(user_data['speed']) + math.sqrt(user_data['dexterity'])
        user.battlescore = battlescore
        user.battlescore_update = utils.now()
        user.save()

        try:
            tornget(f'faction/?selections=positions', user.key, session=reqeusts_session)
        except utils.TornError as e:
            if e.code != 7:
                logger.exception(e)
                honeybadger.notify(e)
                continue
            else:
                if user.factionaa:
                    user.factionaa = False
                    user.save()
                    continue
                else:
                    logger.exception(e)
                    honeybadger.notify(e)
                    continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)

            if user.factionaa:
                user.factionaa = False
                user.save()

            continue

        user.factionaa = True
        user.save()
