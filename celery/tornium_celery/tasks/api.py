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

import datetime
import json

if globals().get("orjson:loaded"):
    import orjson

import requests
from tornium_commons import Config, rds, with_db_connection
from tornium_commons.errors import (
    DiscordError,
    MissingKeyError,
    NetworkingError,
    RatelimitError,
    TornError,
)
from tornium_commons.models import TornKey

import celery
from celery.utils.log import get_task_logger

logger = get_task_logger("celery_app")
config = Config.from_cache()


def discord_request(method: str, endpoint: str, body=None, params=None, headers=None, timeout=5):
    # We want a function to perform a direct Discord request which should only be used for debugging
    # and for paths where ratelimiting doesn't matter
    default_headers = {
        "Authorization": f'Bot {config["bot_token"]}',
        "Content-Type": "application/json",
    }
    merged_headers = {**default_headers, **(headers or {})}

    if body is None or not isinstance(body, dict):
        payload = None
    elif globals().get("orjson:loaded"):
        payload = orjson.dumps(body)
    else:
        payload = json.dumps(body)

    return requests.request(
        method=method.upper(),
        url=f"https://discord.com/api/v10/{endpoint}",
        params=params,
        data=payload,
        headers=merged_headers,
        timeout=timeout,
    )


@celery.shared_task(name="tasks.api.tornget", time_limit=5, routing_key="api.tornget", queue="api")
@with_db_connection
def tornget(endpoint, key, tots=0, fromts=0, stat="", session=None, pass_error=False, version=1):
    url = (
        f'{config.torn_api_uri}v{version}/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}'
        f'{"" if tots == 0 else f"&to={tots}"}{stat if stat == "" else f"&stat={stat}"}'
    )

    if key is None or key == "":
        raise MissingKeyError

    redis_client = rds()
    redis_key = f"tornium:torn-ratelimit:{key}"
    ttl = 60 - datetime.datetime.utcnow().second

    redis_client.set(redis_key, 50, nx=True, ex=ttl)

    try:
        if int(redis_client.get(redis_key)) > 0:
            redis_client.decrby(redis_key, 1)
            redis_client.expire(redis_key, ttl, nx=True)
        else:
            if redis_client.ttl(redis_key) == -1:
                redis_client.set(redis_key, 1, ex=ttl)

            raise RatelimitError
    except TypeError:
        redis_client.set(redis_key, 50, nx=True, ex=ttl)

    try:
        if session is None:
            request = requests.get(url, timeout=5)
        else:
            request = session.get(url, timeout=5)
    except requests.exceptions.Timeout:
        raise NetworkingError(code=408, url=url)

    if request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    if globals().get("orjson:loaded"):
        request = orjson.loads(request.content)
    else:
        request = request.json()

    if "error" in request:
        if request["error"]["code"] in (
            2,  # Incorrect key
            10,  # Key owner is in federal jail
            13,  # Key disabled due to owner inactivity
            18,  # API key paused by owner
        ):
            # TODO: Add proper support for pausing API key with restoring when the key has been unpaused
            #
            # Delete the API key
            # WIth these errors, it'll hurt more to keep the API key rather than removing it and letting the person sign in later
            TornKey.delete().where(TornKey.api_key == key).execute()

        if not pass_error:
            raise TornError(code=request["error"]["code"], endpoint=url)

    return request


def discord_do(method, endpoint, body=None):
    payload = {"method": method, "endpoint": "/" + endpoint}

    if body is not None:
        payload["body"] = body

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    return requests.post("http://localhost:4000/discord", headers={"Content-Type": "application/json"}, data=payload)


@celery.shared_task(
    name="tasks.api.discordget",
    bind=True,
    max_retries=2,
    routing_key="api.discordget",
    queue="api",
    time_limit=10,
)
def discordget(self: celery.Task, endpoint, *args, **kwargs):
    request = discord_do("GET", endpoint)

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=endpoint)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=endpoint)

    return request_json


@celery.shared_task(
    name="tasks.api.discordpatch",
    bind=True,
    max_retries=2,
    routing_key="api.discordpatch",
    queue="api",
    time_limit=10,
)
def discordpatch(self, endpoint, payload, *args, **kwargs):
    request = discord_do("PATCH", endpoint, payload)

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=endpoint)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=endpoint)

    return request_json


@celery.shared_task(
    name="tasks.api.discordpost",
    bind=True,
    max_retries=2,
    routing_key="api.discordpost",
    queue="api",
    time_limit=10,
)
def discordpost(self, endpoint, payload, *args, **kwargs):
    request = discord_do("POST", endpoint, payload)

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=endpoint)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=endpoint)

    return request_json


@celery.shared_task(
    name="tasks.api.discordput",
    bind=True,
    max_retries=2,
    routing_key="api.discordput",
    queue="api",
)
def discordput(self, endpoint, payload, *args, **kwargs):
    request = discord_do("PUT", endpoint, payload)

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=endpoint)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=endpoint)

    return request_json


@celery.shared_task(
    name="tasks.api.discorddelete",
    bind=True,
    max_retries=2,
    routing_key="api.discorddelete",
    queue="api",
    time_limit=5,
)
def discorddelete(self, endpoint, *args, **kwargs):
    request = discord_do("DELETE", endpoint)

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=endpoint)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=endpoint)

    return request_json


@celery.shared_task(
    name="tasks.api.torn_stats_get",
    time_limit=15,
    routing_key="api.torn_stats_get",
    queue="api",
)
def torn_stats_get(endpoint, key, session=None):
    url = f"https://www.tornstats.com/api/v2/{key}/{endpoint}"
    redis_key = f"tornium:ts-ratelimit:{key}"
    redis_client = rds()

    redis_client.set(redis_key, 15, nx=True, ex=60 - datetime.datetime.utcnow().second)

    if redis_client.ttl(redis_key) < 1:
        redis_client.expire(redis_key, 1)
        redis_client.set(redis_key, 50, nx=True, ex=60 - datetime.datetime.utcnow().second)

    if int(redis_client.get(redis_key)) > 0:
        redis_client.decrby(redis_key, 1)
    else:
        raise RatelimitError

    try:
        if session is None:
            request = requests.get(url, timeout=15)
        else:
            request = session.get(url, timeout=15)
    except requests.exceptions.Timeout:
        raise NetworkingError(code=408, url=url)

    if request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    if globals().get("orjson:loaded"):
        request = orjson.loads(request.content)
    else:
        request = request.json()

    return request
