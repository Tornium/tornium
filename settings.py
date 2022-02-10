# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json
import os

from redisdb import get_redis


try:
    file = open('settings.json')
    file.close()
except FileNotFoundError:
    data = {
        'jsonfiles': ['settings'],
        'dev': False,
        'bottoken': '',
        'secret': str(os.urandom(32)),
        'taskqueue': 'redis',
        'username': 'tornium',
        'password': '',
        'host': '',
        'url': '',
        'honeyenv': 'production',
        'honeykey': '',
        'honeysitecheckin': '',
        'honeybotcheckin': '',
    }
    with open(f'settings.json', 'w') as file:
        json.dump(data, file, indent=4)

with open('settings.json', 'r') as file:
    data = json.load(file)

redis = get_redis()
redis.set('tornium:settings:dev', str(data.get('dev')))
redis.set('tornium:settings:bottoken', data.get('bottoken'))
redis.set('tornium:settings:secret', data.get('secret'))
redis.set('tornium:settings:taskqueue', data.get('taskqueue'))
redis.set('tornium:settings:username', data.get('username'))
redis.set('tornium:settings:password', data.get('password'))
redis.set('tornium:settings:host', data.get('host'))
redis.set('tornium:settings:url', data.get('url'))
redis.set('tornium:settings:honeyenv', data.get('honeyenv'))
redis.set('tornium:settings:honeykey', data.get('honeykey'))
redis.set('tornium:settings:honeysitecheckin', data.get('honeysitecheckin'))
redis.set('tornium:settings:honeybotcheckin', data.get('honeybotcheckin'))
