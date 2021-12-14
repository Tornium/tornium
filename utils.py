# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster.deeksh@gmail.com>

import datetime
import logging
import time

import requests

from redisdb import get_redis


class NetworkingError(Exception):
    pass


class TornError(Exception):
    pass


def get_logger():
    return logging.getLogger("server")


def tornget(endpoint, key, tots=0, fromts=0, stat='', session=None):
    url = f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}' \
          f'{"" if tots == 0 else f"&to={tots}"}{stat if stat == "" else f"stat={stat}"}'

    if key is None or key == '':
        raise Exception

    redis = get_redis()
    if redis.setnx(key, 100):
        redis.expire(key, 60 - datetime.datetime.utcnow().second)
    if redis.ttl(key) < 0:
        redis.expire(key, 1)

    if redis.get(key) and int(redis.get(key)) > 0:
        redis.decrby(key, 1)
    else:
        time.sleep(60 - datetime.datetime.utcnow().second)

    if session is None:  # Utilizes https://docs.python-requests.org/en/latest/user/advanced/#session-objects
        request = requests.get(url)
    else:
        request = session.get(url)

    if request.status_code != 200:
        get_logger().warning(f'The Torn API has responded with status code {request.status_code} to endpoint '
                             f'"{endpoint}".')
        raise NetworkingError(request.status_code)

    request = request.json()

    if 'error' in request:
        get_logger().info(f'The Torn API has responded with error code {request["error"]["code"]} '
                          f'({request["error"]["error"]}) to {url}).')
        raise TornError(request["error"]["code"])

    return request


def now():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())


def remove_str(text):
    return int(''.join(filter(lambda x: x.isdigit(), text)))


def rel_time(time):
    delta = now() - int(time.timestamp())

    if delta < 60:  # One minute
        return 'Now'
    elif delta < 3600:  # Sixty minutes
        if int(round(delta/60)) == 1:
            return f'{int(round(delta/60))} minute ago'
        else:
            return f'{int(round(delta/60))} minutes ago'
    elif delta < 86400:  # One day
        if int(round(delta/3600)) == 1:
            return f'{int(round(delta/3600))} hours ago'
        else:
            return f'{int(round(delta/3600))} hours ago'
    elif delta < 2592000:  # Thirty days
        if int(round(delta/86400)) == 1:
            return f'{int(round(delta/86400))} day ago'
        else:
            return f'{int(round(delta/86400))} days ago'
    else:
        return 'A long time ago'


def torn_timestamp(timestamp=None):
    if timestamp is None:
        return datetime.datetime.utcnow().strftime('%m/%d %H:%M:%S TCT')
    else:
        return datetime.datetime.fromtimestamp(timestamp).strftime('%m/%d %H:%M:%S TCT')


def remove_html(text):
    cleaner = re.compile("<.*?>")
    return re.sub(cleaner, '', text)


def first(array):
    return None if len(array) == 0 else array[0]

