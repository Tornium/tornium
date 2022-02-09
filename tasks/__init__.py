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

import datetime
import logging
import json
import time

from celery import Celery
from celery.schedules import crontab
import honeybadger
from mongoengine import connect
import requests

import settings  # Do not remove - initializes redis values
from models.factionmodel import FactionModel
from models.servermodel import ServerModel
from models.usermodel import UserModel
from redisdb import get_redis
import utils
from utils.errors import DiscordError, MissingKeyError, NetworkingError, RatelimitError, TornError

honeybadger.honeybadger.configure(api_key=get_redis().get('tornium:settings:honeykey'))

connect(
    db='Tornium',
    username=get_redis().get('tornium:settings:username'),
    password=get_redis().get('tornium:settings:password'),
    host=f'mongodb://{get_redis().get("tornium:settings:host")}',
    connect=False
)

celery_app: Celery = None
logger: logging.Logger = logging.getLogger('celery')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='celeryerrors.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


if celery_app is None:
    try:
        file = open('celery.json')
        file.close()
    except FileNotFoundError:
        data = {  # Miscellaneous tasks
            'honeybadger-site-checkin': {
                'task': 'tasks.honeybadger_site_checkin',
                'enabled': False,
                'schedule': {
                    'type': 'cron',
                    'minute': '*',
                    'hour': '*'
                }
            },  # Faction tasks
            'refresh-factions': {
                'task': 'tasks.faction.refresh_factions',
                'enabled': True,
                'schedule': {
                    'type': 'cron',
                    'minute': '0',
                    'hour': '*'
                }
            },
            'fetch-attacks': {
                'task': 'tasks.faction.fetch_attacks',
                'enabled': True,
                'schedule': {
                    'type': 'cron',
                    'minute': '0',
                    'hour': '*'
                }
            },  # Guild tasks
            'refresh-guilds': {
                'task': 'tasks.guild.refresh_guilds',
                'enabled': True,
                'schedule': {
                    'type': 'cron',
                    'minute': '0',
                    'hour': '*'
                }
            },
            'user-stakeouts': {
                'task': 'tasks.stakeouts.user_stakeouts',
                'enabled': True,
                'schedule': {
                    'type': 'cron',
                    'minute': '*',
                    'hour': '*'
                }
            },
            'faction-stakeouts': {
                'task': 'tasks.stakeouts.faction_stakeouts',
                'enabled': True,
                'schedule': {
                    'type': 'cron',
                    'minute': '*',
                    'hour': '*'
                }
            },
            'refresh-users': {
                'task': 'tasks.user.refresh_users',
                'enabled': True,
                'schedule': {
                    'type': {
                        'type': 'cron',
                        'minute': '*/5',
                        'hour': '*'
                    }
                }
            }
        }

        with open('celery.json', 'w') as file:
            json.dump(data, file, indent=4)

    with open('celery.json', 'r') as file:
        data = json.load(file)

    celery_app = Celery(
        'tasks',
        backend='redis://localhost:6379/0',
        broker='redis://localhost:6379/0',
        include=['tasks', 'tasks.faction', 'tasks.guild', 'tasks.stakeouts', 'tasks.user']
    )
    celery_app.conf.update(
        task_serializer='json',
        result_serializer='json'
    )
    celery_app.conf.timezone = 'UTC'

    schedule = {}

    if data['honeybadger-site-checkin']['enabled']:
        schedule['honeybadger-site-checkin'] = {
            'task': data['honeybadger-site-checkin']['task'],
            'schedule': crontab(
                minute=data['honeybadger-site-checkin']['schedule']['minute'],
                hour=data['honeybadger-site-checkin']['schedule']['hour']
            )
        }
    if data['refresh-factions']['enabled']:
        schedule['refresh-factions'] = {
            'task': data['refresh-factions']['task'],
            'schedule': crontab(
                minute=data['refresh-factions']['schedule']['minute'],
                hour=data['refresh-factions']['schedule']['hour']
            )
        }
    if data['fetch-attacks']['enabled']:
        schedule['fetch-attacks'] = {
            'task': data['fetch-attacks']['task'],
            'schedule': crontab(
                minute=data['fetch-attacks']['schedule']['minute'],
                hour=data['refresh-factions']['schedule']['hour']
            )
        }
    if data['refresh-guilds']['enabled']:
        schedule['refresh-guilds'] = {
            'task': data['refresh-guilds']['task'],
            'schedule': crontab(
                minute=data['refresh-guilds']['schedule']['minute'],
                hour=data['refresh-guilds']['schedule']['hour']
            )
        }
    if data['user-stakeouts']['enabled']:
        schedule['user-stakeouts'] = {
            'task': data['user-stakeouts']['task'],
            'schedule': crontab(
                minute=data['user-stakeouts']['schedule']['minute'],
                hour=data['user-stakeouts']['schedule']['hour']
            )
        }
    if data['faction-stakeouts']['enabled']:
        schedule['faction-stakeouts'] = {
            'task': data['faction-stakeouts']['task'],
            'schedule': crontab(
                minute=data['faction-stakeouts']['schedule']['minute'],
                hour=data['faction-stakeouts']['schedule']['hour']
            )
        }
    if data['refresh-users']['enabled']:
        schedule['refresh-users'] = {
            'task': data['refresh-users']['task'],
            'schedule': crontab(
                minute=data['refresh-users']['schedule']['minute'],
                hour=data['refresh-users']['schedule']['hour']
            )
        }

    celery_app.conf.beat_schedule = schedule


@celery_app.task
def tornget(endpoint, key, tots=0, fromts=0, stat='', session=None, autosleep=False):
    url = f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}' \
          f'{"" if tots == 0 else f"&to={tots}"}{stat if stat == "" else f"&stat={stat}"}'
    logger.info(f'The API call has been made to {url}).')

    if key is None or key == '':
        raise MissingKeyError
    
    redis = get_redis()
    redis_key = f'tornium:torn-ratelimit:{key}'

    if redis.setnx(redis_key, 100):
        redis.expire(redis_key, 60 - datetime.datetime.utcnow().second)
    if redis.ttl(redis_key) < 0:
        redis.expire(redis_key, 1)
    
    try:
        if redis.get(redis_key) is not None and int(redis.get(redis_key)) > 0:
            redis.decrby(redis_key, 1)
        else:
            if autosleep:
                time.sleep(60 - datetime.datetime.utcnow().second)
            else:
                raise RatelimitError
    except TypeError as e:
        logger.warning(f'Error raised on API key {key}')
        raise e
    
    if session is None:
        request = requests.get(url)
    else:
        request = session.get(url)
    
    if request.status_code != 200:
        logger.warning(f'The Torn API has responded with status code {request.status_code} to endpoint "{endpoint}".')
        raise NetworkingError(
            code=request.status_code
        )
    
    request = request.json()

    if 'error' in request:
        if request['error']['code'] in (13, 10, 2):
            user = utils.first(UserModel.objects(key=key))
            
            if user is not None:
                factions = FactionModel.objects(keys=key)

                faction: FactionModel
                for faction in factions:
                    faction.keys.remove(key)
                    faction.save()

                user.key = ''
                user.save()

                for server in user.servers():
                    server = utils.first(ServerModel.objects(sid=server))

                    if server is not None and user.tid in server.admins:
                        server.admins.remove(user.tid)
                    server.save()
                
                for server in ServerModel.objects(admins=user.tid):
                    server.admins.remove(user.tid)
                    server.save()
            else:
                factions = FactionModel.objects(keys=key)

                faction: FactionModel
                for faction in factions:
                    faction.keys.remove(key)
                    faction.save()
        elif request['error']['code'] == 7:
            user: UserModel = utils.first(UserModel.objects(key=key))
            user.factionaa = False
            user.save()

            faction: FactionModel
            for faction in FactionModel.objects(keys=key):
                faction.keys.remove(key)
                faction.save()
        
        logger.info(f'The Torn API has responded with error code {request["error"]["code"]} '
                    f'({request["error"]["error"]}) to {url}).')
        raise TornError(
            code=request["error"]["code"]
        )
    
    return request


@celery_app.task
def discordget(endpoint, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'
    redis = get_redis()

    headers = {
        'Authorization': f'Bot {redis.get("tornium:settings:bottoken")}'
    }

    if session is None:
        request = requests.get(url, headers=headers)
    else:
        request = session.get(url, headers=headers)
    
    try:
        request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            logger.warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint "{endpoint}".'
            )
            raise NetworkingError(
                code=request.status_code
            )
        else:
            raise e
    
    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error code
        # explanations

        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} to {url}).'
        )
        logger.debug(request_json)
        raise DiscordError(
            code=request_json['code'],
            message=request_json["message"]
        )
    elif request.status_code // 100 != 2:
        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} to {url}).'
        )
        raise NetworkingError(
            code=request.status_code
        )
    
    return request_json


@celery_app.task
def discordpost(endpoint, payload, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'
    redis = get_redis()

    headers = {
        'Authorization': f'Bot {redis.get("tornium:settings:bottoken")}',
        'Content-Type': 'application/json'
    }

    if session is None:
        request = requests.post(url, headers=headers, data=json.dumps(payload))
    else:
        request = session.post(url, headers=headers, data=json.dumps(payload))
    
    try:
        request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            logger.warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint "{endpoint}".'
            )
            raise NetworkingError(
                code=request.status_code
            )
        else:
            raise e
    
    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error code
        # explanations

        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} to {url}).'
        )
        logger.debug(request_json)
        raise DiscordError(
            code=request_json['code'],
            message=request_json['message']
        )
    elif request.status_code // 100 != 2:
        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} to {url}).'
        )
        raise NetworkingError(
            code=request.status_code
        )
    
    return request_json


@celery_app.task
def discorddelete(endpoint, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'
    redis = get_redis()

    headers = {
        'Authorization': f'Bot {redis.get("tornium:settings:bottoken")}',
        'Content-Type': 'application/json'
    }

    if session is None:
        request = requests.delete(url, headers=headers)
    else:
        request = session.delete(url, headers=headers)
    
    try:
        request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            logger.warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint "{endpoint}".'
            )
            raise NetworkingError(
                code=request.status_code
            )
        else:
            raise e
    
    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error code
        # explanations

        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} to {url}).'
        )
        logger.debug(request_json)
        raise DiscordError(
            code=request_json['code'],
            message=request_json['message']
        )
    elif request.status_code // 100 != 2:
        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} to {url}).'
        )
        raise NetworkingError(
            code=request.status_code
        )
    
    return request_json


@celery_app.task
def torn_stats_get(endpoint, key, session=None, autosleep=False):
    url = f'https://www.tornstats.com/api/v2/{key}/{endpoint}'

    redis = get_redis()
    redis_key = f'tornium:ts-ratelimit:{key}'

    if redis.get(redis_key) is None:
        redis.set(redis_key, 15)
        redis.expire(redis_key, 60 - datetime.datetime.utcnow().second)
    if redis.ttl(redis_key) < 0:
        redis.expire(redis_key, 1)

    if redis.get(redis_key) is not None and int(redis.get(redis_key)) > 0:
        redis.decrby(redis_key, 1)
    else:
        if autosleep:
            time.sleep(60 - datetime.datetime.utcnow().second)
        else:
            raise RatelimitError
    
    if session is None:
        request = requests.get(url)
    else:
        request = session.get(url)
    
    if request.status_code // 100 != 200:
        logger.warning(f'The Torn Stats API has responded with HTTP status code {request.status_code} to endpoint "{endpoint}".')
        raise NetworkingError(code=request.status_code)
    
    request = request.json()
    return request


@celery_app.task
def honeybadger_site_checkin():
    redis = get_redis()

    if redis.get('tornium:settings:honeysitecheckin') is None or redis.get('tornium:settings:honeysitecheckin') == '':
        return
    elif redis.get('tornium:settings:url') is None or redis.get('tornium:settins:url') == '':
        return

    site = requests.get(redis.get('tornium:settings:url'))

    if site.status_code != requests.codes.ok:
        return

    requests.get(redis.get('tornium:settings:honeysitecheckin'))
