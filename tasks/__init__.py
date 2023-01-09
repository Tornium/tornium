# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import sys

if not hasattr(sys, "_called_from_test"):
    from ddtrace import patch_all

    patch_all(logging=True)
    import ddtrace.profiling.auto


import datetime
import logging
import json
import math
import time

from celery import Celery
from celery.schedules import crontab
from mongoengine import connect
from redis.commands.json.path import Path
import requests

import settings  # Do not remove - initializes redis values
from redisdb import get_redis
from utils.errors import (
    DiscordError,
    MissingKeyError,
    NetworkingError,
    RatelimitError,
    TornError,
)

if not hasattr(sys, "_called_from_test"):
    connect(
        db="Tornium",
        username=get_redis().get("tornium:settings:username"),
        password=get_redis().get("tornium:settings:password"),
        host=f'mongodb://{get_redis().get("tornium:settings:host")}',
        connect=False,
    )

FORMAT = (
    "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] "
    "[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%"
    "(dd.span_id)s] - %(message)s"
)

celery_app: Celery = None
logger: logging.Logger = logging.getLogger("celeryerrors")
if get_redis().get("dev"):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="celeryerrors.log", encoding="utf-8", mode="a")
handler.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(handler)


if celery_app is None:
    try:
        file = open("celery.json")
        file.close()
    except FileNotFoundError:
        data = {  # Faction tasks
            "refresh-factions": {
                "task": "tasks.faction.refresh_factions",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "5", "hour": "*"},
            },
            "fetch-attacks-runner": {
                "task": "tasks.faction.fetch_attacks_runner",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },
            "oc-refresh": {
                "task": "tasks.faction.oc_refresh",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/5", "hour": "*"},
            },  # Guild tasks
            "refresh-guilds": {
                "task": "tasks.guild.refresh_guilds",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "0", "hour": "*"},
            },
            "user-stakeouts": {
                "task": "tasks.stakeouts.user_stakeouts",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },
            "faction-stakeouts": {
                "task": "tasks.stakeouts.faction_stakeouts",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },  # User tasks
            "refresh-users": {
                "task": "tasks.user.refresh_users",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/10", "hour": "*"},
            },
            "fetch-attacks-users": {
                "task": "tasks.user.fetch_attacks_users",
                "enabled": False,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },  # Stock tasks
            "fetch-stock-ticks": {
                "task": "tasks.stocks.fetch_stock_ticks",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },
        }

        with open("celery.json", "w") as file:
            json.dump(data, file, indent=4)

    with open("celery.json", "r") as file:
        data = json.load(file)

    celery_app = Celery(
        "tasks",
        backend="redis://localhost:6379/0",
        broker="redis://localhost:6379/0",
        include=[
            "tasks",
            "tasks.faction",
            "tasks.guild",
            "tasks.stakeouts",
            "tasks.stocks",
            "tasks.user",
        ],
    )
    celery_app.conf.update(task_serializer="json", result_serializer="json")
    celery_app.conf.timezone = "UTC"

    schedule = {}

    if "refresh-factions" in data and data["refresh-factions"]["enabled"]:
        schedule["refresh-factions"] = {
            "task": data["refresh-factions"]["task"],
            "schedule": crontab(
                minute=data["refresh-factions"]["schedule"]["minute"],
                hour=data["refresh-factions"]["schedule"]["hour"],
            ),
        }
    if "fetch-attacks-runner" in data and data["fetch-attacks-runner"]["enabled"]:
        schedule["fetch-attacks-runner"] = {
            "task": data["fetch-attacks-runner"]["task"],
            "schedule": crontab(
                minute=data["fetch-attacks-runner"]["schedule"]["minute"],
                hour=data["fetch-attacks-runner"]["schedule"]["hour"],
            ),
        }
    if "oc-refresh" in data and data["oc-refresh"]["enabled"]:
        schedule["oc-refresh"] = {
            "task": data["oc-refresh"]["task"],
            "schedule": crontab(
                minute=data["oc-refresh"]["schedule"]["minute"],
                hour=data["oc-refresh"]["schedule"]["hour"],
            ),
        }
    if "refresh-guilds" in data and data["refresh-guilds"]["enabled"]:
        schedule["refresh-guilds"] = {
            "task": data["refresh-guilds"]["task"],
            "schedule": crontab(
                minute=data["refresh-guilds"]["schedule"]["minute"],
                hour=data["refresh-guilds"]["schedule"]["hour"],
            ),
        }
    if "user-stakeouts" in data and data["user-stakeouts"]["enabled"]:
        schedule["user-stakeouts"] = {
            "task": data["user-stakeouts"]["task"],
            "schedule": crontab(
                minute=data["user-stakeouts"]["schedule"]["minute"],
                hour=data["user-stakeouts"]["schedule"]["hour"],
            ),
        }
    if "faction-stakeouts" in data and data["faction-stakeouts"]["enabled"]:
        schedule["faction-stakeouts"] = {
            "task": data["faction-stakeouts"]["task"],
            "schedule": crontab(
                minute=data["faction-stakeouts"]["schedule"]["minute"],
                hour=data["faction-stakeouts"]["schedule"]["hour"],
            ),
        }
    if "refresh-users" in data and data["refresh-users"]["enabled"]:
        schedule["refresh-users"] = {
            "task": data["refresh-users"]["task"],
            "schedule": crontab(
                minute=data["refresh-users"]["schedule"]["minute"],
                hour=data["refresh-users"]["schedule"]["hour"],
            ),
        }
    if "fetch-attacks-users" in data and data["fetch-attacks-users"]["enabled"]:
        schedule["fetch-attacks-users"] = {
            "task": data["fetch-attacks-users"]["task"],
            "schedule": crontab(
                minute=data["fetch-attacks-users"]["schedule"]["minute"],
                hour=data["fetch-attacks-users"]["schedule"]["hour"],
            ),
        }
    if "fetch-stock-ticks" in data and data["fetch-stock-ticks"]["enabled"]:
        schedule["fetch-stock-ticks"] = {
            "task": data["fetch-stock-ticks"]["task"],
            "schedule": crontab(
                minute=data["fetch-stock-ticks"]["schedule"]["minute"],
                hour=data["fetch-stock-ticks"]["schedule"]["hour"],
            ),
        }

    celery_app.conf.beat_schedule = schedule


@celery_app.task(time_limit=5)  # Prevents task for running for more than five seconds
def tornget(
    endpoint,
    key,
    tots=0,
    fromts=0,
    stat="",
    session=None,
    autosleep=True,
    cache=30,
    nocache=False,
):
    url = (
        f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}'
        f'{"" if tots == 0 else f"&to={tots}"}{stat if stat == "" else f"&stat={stat}"}'
    )

    if key is None or key == "":
        raise MissingKeyError

    redis = get_redis()

    if redis.exists(f"tornium:torn-cache:{url}") and not nocache:
        return redis.json().get(f"tornium:torn-cache:{url}")

    redis_key = f"tornium:torn-ratelimit:{key}"

    if redis.setnx(redis_key, 50):
        redis.expire(redis_key, 60 - datetime.datetime.utcnow().second)
    if redis.ttl(redis_key) < 0:
        redis.expire(redis_key, 1)
        redis.set(redis_key, 50)
        redis.expire(redis_key, 60 - datetime.datetime.utcnow().second)

    try:
        if redis.get(redis_key) is not None and int(redis.get(redis_key)) > 0:
            redis.decrby(redis_key, 1)
        else:
            if autosleep:
                time.sleep(60 - datetime.datetime.utcnow().second)
            else:
                if redis.get(redis_key) is None:
                    redis.set(redis_key, 50)
                    redis.expire(redis_key, 60 - datetime.datetime.utcnow().second)
                else:
                    raise RatelimitError
    except TypeError:
        logger.warning(
            f"Error raised on API key {key} with redis return value {redis.get(redis_key)} and redis key {redis_key}"
        )

    try:
        if session is None:
            request = requests.get(url, timeout=5)
        else:
            request = session.get(url, timeout=5)
    except requests.exceptions.Timeout as e:
        logger.exception(e)
        raise NetworkingError(code=408, url=url)

    if request.status_code != 200:
        logger.warning(f'The Torn API has responded with status code {request.status_code} to endpoint "{endpoint}".')
        raise NetworkingError(code=request.status_code, url=url)

    request = request.json()

    if "error" in request:
        logger.info(
            f'The Torn API has responded with error code {request["error"]["code"]} '
            f'({request["error"]["error"]}) to {url}).'
        )
        raise TornError(code=request["error"]["code"], endpoint=url)

    if cache <= 0 or cache >= 60:
        return request
    elif sys.getsizeof(request) >= 500000:  # Half a megabyte
        return request

    redis.json().set(f"tornium:torn-cache:{url}", Path.root_path(), request)
    redis.expire(f"tornium:torn-cache:{url}", cache)

    return request


@celery_app.task(bind=True, max_retries=3)
def discordget(self, endpoint, session=None, bucket=None, retry=False):
    redis = get_redis()

    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {"Authorization": f'Bot {redis.get("tornium:settings:skynet:bottoken")}'}

    if redis.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError()
    elif (
        bucket is not None
        and redis.exists(f"tornium:discord:ratelimit:bucket:{bucket}")
        and int(redis.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0
        and redis.ttl(f"tornium:discord:ratelimit:bucket{bucket}") > 0
    ):
        if retry:
            self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
        else:
            raise RatelimitError()

    if session is None:
        request = requests.get(url, headers=headers)
    else:
        request = session.get(url, headers=headers)

    if request.status_code == 429:
        logger.warning(f"The Discord API has ratelimited endpoint {endpoint}.")

        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis.exists("tornium:discord:ratelimit:global")
        ):
            redis.setnx("tornium:discord:ratelimit:global", 1)
            redis.expire(
                "tornium:discord:ratelimit:global",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning("The Discord API has enabled a global ratelimit.")

            if retry:
                self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError()
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis.setnx(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
            )
            redis.expire(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning(f"The Discord API has enabled a bucket ratelimit on bucket {bucket}")

            if retry:
                self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError()
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
        )
        redis.expire(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
        )

    try:
        request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            logger.warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint "{endpoint}".'
            )
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error code
        # explanations

        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} '
            f"to {url})."
        )
        logger.info(request_json)
        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        logger.warning(f"The Discord API has responded with HTTP {request.status_code} to {url}).")
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery_app.task(bind=True, max_retries=3)
def discordpatch(self, endpoint, payload, session=None, bucket=None, retry=False):
    redis = get_redis()

    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {redis.get("tornium:settings:skynet:bottoken")}',
        "Content-Type": "application/json",
    }

    if redis.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError()
    elif (
        bucket is not None
        and redis.exists(f"tornium:discord:ratelimit:bucket:{bucket}")
        and int(redis.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0
        and redis.ttl(f"tornium:discord:ratelimit:bucket{bucket}") > 0
    ):
        if retry:
            self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
        else:
            raise RatelimitError()

    if session is None:
        request = requests.patch(url, headers=headers, data=json.dumps(payload))
    else:
        request = session.patch(url, headers=headers, data=json.dumps(payload))

    if request.status_code == 429:
        logger.warning(f"The Discord API has ratelimited endpoint {endpoint}.")

        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis.exists("tornium:discord:ratelimit:global")
        ):
            redis.setnx("tornium:discord:ratelimit:global", 1)
            redis.expire(
                "tornium:discord:ratelimit:global",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning("The Discord API has enabled a global ratelimit.")

            if retry:
                self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError()
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis.setnx(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
            )
            redis.expire(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning(f"The Discord API has enabled a bucket ratelimit on bucket {bucket}")

            if retry:
                self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError()
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
        )
        redis.expire(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
        )

    try:
        request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            logger.warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint "{endpoint}".'
            )
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error code
        # explanations

        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} '
            f"to {url})."
        )
        logger.info(request_json)
        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        logger.warning(f"The Discord API has responded with HTTP {request.status_code} to {url}).")
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery_app.task(bind=True, max_retries=3)
def discordpost(self, endpoint, payload, session=None, bucket=None, retry=False):
    redis = get_redis()

    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {redis.get("tornium:settings:skynet:bottoken")}',
        "Content-Type": "application/json",
    }

    if redis.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError()
    elif (
        bucket is not None
        and redis.exists(f"tornium:discord:ratelimit:bucket:{bucket}")
        and int(redis.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0
        and redis.ttl(f"tornium:discord:ratelimit:bucket{bucket}") > 0
    ):
        if retry:
            self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
        else:
            raise RatelimitError()

    if session is None:
        request = requests.post(url, headers=headers, data=json.dumps(payload))
    else:
        request = session.post(url, headers=headers, data=json.dumps(payload))

    if request.status_code == 429:
        logger.warning(f"The Discord API has ratelimited endpoint {endpoint}.")

        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis.exists("tornium:discord:ratelimit:global")
        ):
            redis.setnx("tornium:discord:ratelimit:global", 1)
            redis.expire(
                "tornium:discord:ratelimit:global",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning("The Discord API has enabled a global ratelimit.")

            if retry:
                self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError()
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis.setnx(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
            )
            redis.expire(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning(f"The Discord API has enabled a bucket ratelimit on bucket {bucket}")

            if retry:
                self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError()
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
        )
        redis.expire(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
        )

    try:
        request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            logger.warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint "{endpoint}".'
            )
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error code
        # explanations

        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]}) '
            f"to {url})."
        )
        logger.info(request_json)
        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        logger.warning(f"The Discord API has responded with HTTP {request.status_code} to {url}).")
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery_app.task(bind=True, max_retries=3)
def discordput(self, endpoint, payload, session=None, bucket=None, retry=False):
    redis = get_redis()

    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {redis.get("tornium:settings:skynet:bottoken")}',
        "Content-Type": "application/json",
    }

    if redis.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError()
    elif (
        bucket is not None
        and redis.exists(f"tornium:discord:ratelimit:bucket:{bucket}")
        and int(redis.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0
        and redis.ttl(f"tornium:discord:ratelimit:bucket{bucket}") > 0
    ):
        if retry:
            self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
        else:
            raise RatelimitError()

    if session is None:
        request = requests.put(url, headers=headers, data=json.dumps(payload))
    else:
        request = session.put(url, headers=headers, data=json.dumps(payload))

    if request.status_code == 429:
        logger.warning(f"The Discord API has ratelimited endpoint {endpoint}.")

        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis.exists("tornium:discord:ratelimit:global")
        ):
            redis.setnx("tornium:discord:ratelimit:global", 1)
            redis.expire(
                "tornium:discord:ratelimit:global",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning("The Discord API has enabled a global ratelimit.")

            if retry:
                self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError()
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis.setnx(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
            )
            redis.expire(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning(f"The Discord API has enabled a bucket ratelimit on bucket {bucket}")

            if retry:
                self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError()
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
        )
        redis.expire(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
        )

    try:
        request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            logger.warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint "{endpoint}".'
            )
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error code
        # explanations

        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]}) '
            f"to {url})."
        )
        logger.info(request_json)
        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        logger.warning(f"The Discord API has responded with HTTP {request.status_code} to {url}).")
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery_app.task(bind=True, max_retries=3)
def discorddelete(self, endpoint, session=None, bucket=None, retry=False):
    redis = get_redis()

    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {redis.get("tornium:settings:skynet:bottoken")}',
        "Content-Type": "application/json",
    }

    if redis.exists("tornium:discord:ratelimit:global"):
        if retry:
            self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
        else:
            raise RatelimitError()
    elif (
        bucket is not None
        and redis.exists(f"tornium:discord:ratelimit:bucket:{bucket}")
        and int(redis.get(f"tornium:discord:ratelimit:bucket:{bucket}")) <= 0
        and redis.ttl(f"tornium:discord:ratelimit:bucket{bucket}") > 0
    ):
        if retry:
            self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
        else:
            raise RatelimitError()

    if session is None:
        request = requests.delete(url, headers=headers)
    else:
        request = session.delete(url, headers=headers)

    if request.status_code == 429:
        logger.warning(f"The Discord API has ratelimited endpoint {endpoint}.")

        if (
            bucket is not None
            and "X-RateLimit-Global" in request.headers
            and request.headers["X-RateLimit-Global"] in ("true", "True", True)
            and not redis.exists("tornium:discord:ratelimit:global")
        ):
            redis.setnx("tornium:discord:ratelimit:global", 1)
            redis.expire(
                "tornium:discord:ratelimit:global",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning("The Discord API has enabled a global ratelimit.")

            if retry:
                self.retry(countdown=redis.ttl("tornium:discord:ratelimit:global"))
            else:
                raise RatelimitError()
        elif (
            bucket is not None
            and "X-RateLimit-Remaining" in request.headers
            and "X-RateLimit-ResetAfter" in request.headers
        ):
            redis.setnx(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                int(request.headers["X-RateLimit-Remaining"]),
            )
            redis.expire(
                f"tornium:discord:ratelimit:bucket:{bucket}",
                math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
            )
            logger.warning(f"The Discord API has enabled a bucket ratelimit on bucket {bucket}")

            if retry:
                self.retry(countdown=redis.ttl(f"tornium:discord:ratelimit:bucket:{bucket}") + 1)
            else:
                raise RatelimitError()
    elif (
        bucket is not None
        and "X-RateLimit-Remaining" in request.headers
        and "X-RateLimit-ResetAfter" in request.headers
    ):
        redis.set(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            int(request.headers["X-RateLimit-Remaining"]),
        )
        redis.expire(
            f"tornium:discord:ratelimit:bucket:{bucket}",
            math.ceil(float(request.headers["X-RateLimit-ResetAfter"])),
        )

    try:
        request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            logger.warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint "{endpoint}".'
            )
            raise NetworkingError(code=request.status_code, url=url)
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error code
        # explanations

        logger.warning(
            f'The Discord API has responded with error code {request_json["code"]} ({request_json["message"]} '
            f"to {url})."
        )
        logger.info(request_json)
        raise DiscordError(code=request_json["code"], message=request_json["message"])
    elif request.status_code // 100 != 2:
        logger.warning(f"The Discord API has responded with HTTP {request.status_code} to {url}).")
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery_app.task(time_limit=5)
def torn_stats_get(endpoint, key, session=None, autosleep=False):
    url = f"https://www.tornstats.com/api/v2/{key}/{endpoint}"

    redis = get_redis()
    redis_key = f"tornium:ts-ratelimit:{key}"

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
        request = requests.get(url, timeout=3)
    else:
        request = session.get(url, timeout=3)

    if request.status_code // 100 != 2:
        logger.warning(
            f'The Torn Stats API has responded with HTTP status code {request.status_code} to endpoint "{endpoint}".'
        )
        raise NetworkingError(code=request.status_code, url=url)

    request = request.json()
    return request
