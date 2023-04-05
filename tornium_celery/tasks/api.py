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
import math
import time

if globals().get("orjson:loaded"):
    import orjson

import celery
import requests
from tornium_commons import Config, rds
from tornium_commons.errors import (
    DiscordError,
    MissingKeyError,
    NetworkingError,
    RatelimitError,
    TornError,
)

from tornium_celery.tasks.misc import (
    remove_key_error,
    remove_unknown_channel,
    remove_unknown_role,
)


@celery.shared_task(time_limit=5, routing_key="api.tornget", queue="api")
def tornget(
    endpoint,
    key,
    tots=0,
    fromts=0,
    stat="",
    session=None,
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

    if redis_client.ttl(redis_key) < 1:
        redis_client.expire(redis_key, 1)
        redis_client.set(redis_key, 50, nx=True, ex=60 - datetime.datetime.utcnow().second)

    try:
        if int(redis_client.get(redis_key)) > 0:
            redis_client.decrby(redis_key, 1)
        else:
            raise RatelimitError
    except TypeError:
        raise RatelimitError

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
        if request["error"]["code"] in (7, 10, 13):
            remove_key_error.delay(key, request["error"]["code"]).forget()

        raise TornError(code=request["error"]["code"], endpoint=url)

    return request


@celery.shared_task(bind=True, max_retries=3, routing_key="api.discordget", queue="api")
def discordget(self, endpoint, session=None, bucket=None, retry=False, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {"Authorization": f'Bot {Config()["skynet-bottoken"]}'}
    redis_client = rds()

    if redis_client.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError

    try:
        if bucket is not None and int(redis_client.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0:
            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
        elif bucket is not None:  # and bucket > 0
            redis_client.decrby(f"tornium:discord:ratelimit:bucket:{bucket}", 1)
    except TypeError:
        pass

    if session is None:
        request = requests.get(url, headers=headers)
    else:
        request = session.get(url, headers=headers)

    if request.status_code == 429:
        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis_client.exists("tornium:discord:ratelimit:global")
        ):
            redis_client.set(
                "tornium:discord:ratelimit:global",
                1,
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis_client.set(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis_client.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
            nx=True,
            ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
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

        if request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()
        elif request_json["code"] == 10011:
            if kwargs.get("role") is not None:
                remove_unknown_role.delay(kwargs.get("role")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(bind=True, max_retries=3, routing_key="api.discordpatch", queue="api")
def discordpatch(self, endpoint, payload, session=None, bucket=None, retry=False, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {Config()["skynet-bottoken"]}',
        "Content-Type": "application/json",
    }
    redis_client = rds()

    if redis_client.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError

    try:
        if bucket is not None and int(redis_client.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0:
            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
        elif bucket is not None:  # and bucket > 0
            redis_client.decrby(f"tornium:discord:ratelimit:bucket:{bucket}", 1)
    except TypeError:
        pass

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    if session is None:
        request = requests.patch(url, headers=headers, data=payload)
    else:
        request = session.patch(url, headers=headers, data=payload)

    if request.status_code == 429:
        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis_client.exists("tornium:discord:ratelimit:global")
        ):
            redis_client.set(
                "tornium:discord:ratelimit:global",
                1,
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis_client.set(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis_client.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
            nx=True,
            ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
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

        if request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()
        elif request_json["code"] == 10011:
            if kwargs.get("role") is not None:
                remove_unknown_role.delay(kwargs.get("role")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(bind=True, max_retries=3, routing_key="api.discordpost", queue="api")
def discordpost(self, endpoint, payload, session=None, bucket=None, retry=False, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {Config()["skynet-bottoken"]}',
        "Content-Type": "application/json",
    }
    redis_client = rds()

    if redis_client.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError

    try:
        if bucket is not None and int(redis_client.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0:
            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
        elif bucket is not None:  # and bucket > 0
            redis_client.decrby(f"tornium:discord:ratelimit:bucket:{bucket}", 1)
    except TypeError:
        pass

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    if session is None:
        request = requests.post(url, headers=headers, data=payload)
    else:
        request = session.post(url, headers=headers, data=payload)

    if request.status_code == 429:
        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis_client.exists("tornium:discord:ratelimit:global")
        ):
            redis_client.set(
                "tornium:discord:ratelimit:global",
                1,
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis_client.set(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis_client.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
            nx=True,
            ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
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

        if request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()
        elif request_json["code"] == 10011:
            if kwargs.get("role") is not None:
                remove_unknown_role.delay(kwargs.get("role")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(bind=True, max_retries=3, routing_key="api.discordput", queue="api")
def discordput(self, endpoint, payload, session=None, bucket=None, retry=False, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {Config()["skynet-bottoken"]}',
        "Content-Type": "application/json",
    }
    redis_client = rds()

    if redis_client.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError

    try:
        if bucket is not None and int(redis_client.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0:
            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
        elif bucket is not None:  # and bucket > 0
            redis_client.decrby(f"tornium:discord:ratelimit:bucket:{bucket}", 1)
    except TypeError:
        pass

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    if session is None:
        request = requests.put(url, headers=headers, data=payload)
    else:
        request = session.put(url, headers=headers, data=payload)

    if request.status_code == 429:
        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis_client.exists("tornium:discord:ratelimit:global")
        ):
            redis_client.set(
                "tornium:discord:ratelimit:global",
                1,
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis_client.set(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis_client.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
            nx=True,
            ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
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

        if request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()
        elif request_json["code"] == 10011:
            if kwargs.get("role") is not None:
                remove_unknown_role.delay(kwargs.get("role")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(bind=True, max_retries=3, routing_key="api.discorddelete", queue="api")
def discorddelete(self, endpoint, session=None, bucket=None, retry=False, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {Config()["skynet-bottoken"]}',
        "Content-Type": "application/json",
    }
    redis_client = rds()

    if redis_client.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError

    try:
        if bucket is not None and int(redis_client.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0:
            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
        elif bucket is not None:  # and bucket > 0
            redis_client.decrby(f"tornium:discord:ratelimit:bucket:{bucket}", 1)
    except TypeError:
        pass

    if session is None:
        request = requests.delete(url, headers=headers)
    else:
        request = session.delete(url, headers=headers)

    if request.status_code == 429:
        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis_client.exists("tornium:discord:ratelimit:global")
        ):
            redis_client.set(
                "tornium:discord:ratelimit:global",
                1,
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis_client.set(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
                nx=True,
                ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )

            if retry:
                self.retry(countdown=redis_client.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis_client.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
            nx=True,
            ex=math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
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

        if request_json["code"] == 10003:
            if kwargs.get("channel") is not None:
                remove_unknown_channel.delay(kwargs.get("channel")).forget()
        elif request_json["code"] == 10011:
            if kwargs.get("role") is not None:
                remove_unknown_role.delay(kwargs.get("role")).forget()

        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(time_limit=15, routing_key="api.torn_stats_get", queue="api")
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
