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

import datetime
import json
import random
import typing

if globals().get("orjson:loaded"):
    import orjson

import celery
import requests
from celery.utils.log import get_task_logger
from tornium_commons import Config, DBucket, rds
from tornium_commons.errors import (
    DiscordError,
    MissingKeyError,
    NetworkingError,
    RatelimitError,
    TornError,
)

from .misc import remove_key_error, remove_unknown_channel

logger = get_task_logger("celery_app")


def backoff(self: celery.Task):
    if self.request.retries <= 1:
        return countdown_wo()
    return int(1 + random.uniform(0, self.request.retries) ** self.request.retries)


def countdown_wo():
    return random.randint(1, 3)


def discord_ratelimit_pre(
    self: celery.Task,
    method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"],
    endpoint: str,
    backoff_var: typing.Optional[bool] = True,
):
    if backoff_var is None:
        backoff_var = True

    try:
        bucket = DBucket.from_endpoint(method=method, endpoint=endpoint)
    except RatelimitError:
        raise self.retry(countdown=backoff(self) if backoff_var else countdown_wo())

    logger.warning(f"{method}|{endpoint.split('?')[0]} :: {bucket.remaining}")

    try:
        bucket.call()
    except RatelimitError:
        raise self.retry(countdown=backoff(self) if backoff_var else countdown_wo())

    return bucket


@celery.shared_task(name="tasks.api.tornget", time_limit=5, routing_key="api.tornget", queue="api")
def tornget(
    endpoint,
    key,
    tots=0,
    fromts=0,
    stat="",
    session=None,
    pass_error=False,
):
    url = (
        f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}'
        f'{"" if tots == 0 else f"&to={tots}"}{stat if stat == "" else f"&stat={stat}"}'
    )

    if key is None or key == "":
        raise MissingKeyError

    redis_client = rds()
    redis_key = f"tornium:torn-ratelimit:{key}"

    redis_client.set(redis_key, 50, nx=True, ex=60 - datetime.datetime.utcnow().second)

    try:
        if int(redis_client.get(redis_key)) > 0:
            redis_client.decrby(redis_key, 1)
        else:
            redis_client.set(redis_key, 1, ex=60 - datetime.datetime.utcnow().second)
    except TypeError:
        redis_client.set(redis_key, 50, nx=True, ex=60 - datetime.datetime.utcnow().second)

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

    if "error" in request and not pass_error:
        if request["error"]["code"] in (2, 7, 10, 13):
            remove_key_error.delay(key, request["error"]["code"]).forget()

        raise TornError(code=request["error"]["code"], endpoint=url)

    return request


@celery.shared_task(name="tasks.api.discordget", bind=True, max_retries=5, routing_key="api.discordget", queue="api")
def discordget(self: celery.Task, endpoint, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {"Authorization": f'Bot {Config()["skynet-bottoken"]}'}

    bucket = discord_ratelimit_pre(self, "GET", endpoint, backoff_var=kwargs.get("backoff", True))

    request = requests.get(url, headers=headers)

    bucket.update_bucket(request.headers, "GET", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(), exc=RatelimitError()
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)
        elif request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(
    name="tasks.api.discordpatch", bind=True, max_retries=5, routing_key="api.discordpatch", queue="api"
)
def discordpatch(self, endpoint, payload, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {Config()["skynet-bottoken"]}',
        "Content-Type": "application/json",
    }

    bucket = discord_ratelimit_pre(self, "PATCH", endpoint, backoff_var=kwargs.get("backoff", True))

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    request = requests.patch(url, headers=headers, data=payload)

    bucket.update_bucket(request.headers, "PATCH", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(), exc=RatelimitError()
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)
        elif request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(name="tasks.api.discordpost", bind=True, max_retries=5, routing_key="api.discordpost", queue="api")
def discordpost(self, endpoint, payload, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {Config()["skynet-bottoken"]}',
        "Content-Type": "application/json",
    }

    bucket = discord_ratelimit_pre(self, "POST", endpoint, backoff_var=kwargs.get("backoff", True))

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    request = requests.post(url, headers=headers, data=payload)

    bucket.update_bucket(request.headers, "GET", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(), exc=RatelimitError()
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)
        elif request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(name="tasks.api.discordput", bind=True, max_retries=5, routing_key="api.discordput", queue="api")
def discordput(self, endpoint, payload, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {Config()["skynet-bottoken"]}',
        "Content-Type": "application/json",
    }

    bucket = discord_ratelimit_pre(self, "PUT", endpoint, backoff_var=kwargs.get("backoff", True))

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    request = requests.put(url, headers=headers, data=payload)

    bucket.update_bucket(request.headers, "GET", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(), exc=RatelimitError()
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)
        elif request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(
    name="tasks.api.discorddelete", bind=True, max_retries=5, routing_key="api.discorddelete", queue="api"
)
def discorddelete(self, endpoint, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {Config()["skynet-bottoken"]}',
        "Content-Type": "application/json",
    }

    bucket = discord_ratelimit_pre(self, "GET", endpoint, backoff_var=kwargs.get("backoff", True))

    request = requests.delete(url, headers=headers)

    bucket.update_bucket(request.headers, "GET", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(), exc=RatelimitError()
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)
        elif request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(name="tasks.api.torn_stats_get", time_limit=15, routing_key="api.torn_stats_get", queue="api")
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
