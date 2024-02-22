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

import base64
import datetime
import time
import typing
from functools import partial, wraps

import msgpack
import redis
from flask import Response, jsonify, request, session
from flask_login import current_user
from peewee import DoesNotExist
from tornium_commons import rds
from tornium_commons.models import TornKey, User

from controllers.api.v1.utils import make_exception_response


def ratelimit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        client = rds()
        key = f'tornium:ratelimit:{kwargs["user"].tid}'
        limit = 250

        if client.setnx(key, limit):
            client.expire(key, 60 - datetime.datetime.utcnow().second)

        value = client.get(key)

        if client.ttl(key) < 0:
            client.expire(key, 1)

        if value and int(value) > 0:
            client.decrby(key, 1)
        else:
            return make_exception_response("4000", key)

        return func(*args, **kwargs)

    return wrapper


def torn_key_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        if request.headers.get("Authorization") is None:
            return make_exception_response("4001")
        elif request.headers.get("Authorization").split(" ")[0] != "Basic":
            return make_exception_response("4003")

        authorization = str(
            base64.b64decode(request.headers.get("Authorization").split(" ")[1]),
            "utf-8",
        ).split(
            ":"
        )[0]

        if authorization == "":
            return make_exception_response("4001")

        try:
            user: User = TornKey.select().where(TornKey.api_key == authorization).get().user
        except DoesNotExist:
            return make_exception_response("4001")

        kwargs["user"] = user
        kwargs["key"] = authorization
        kwargs["start_time"] = start_time

        return func(*args, **kwargs)

    return wrapper


def session_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        if not current_user.is_authenticated:
            return make_exception_response("4001")

        csrf_token = request.headers.get("X-CSRF-Token") or request.headers.get("CSRF-Token")

        if csrf_token != session.get("csrf_token"):
            return make_exception_response("4002")

        kwargs["user"] = current_user
        kwargs["key"] = current_user.key
        kwargs["start_time"] = start_time

        return func(*args, **kwargs)

    return wrapper


def authentication_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        if request.headers.get("Authorization") is None and not current_user.is_authenticated:
            return make_exception_response("4001")

        if current_user.is_authenticated:
            csrf_token = request.headers.get("X-CSRF-Token") or request.headers.get("CSRF-Token")

            if csrf_token != session.get("csrf_token"):
                return make_exception_response("4002")

            kwargs["user"] = current_user
            kwargs["key"] = current_user.key
            kwargs["start_time"] = start_time

            return func(*args, **kwargs)

        authorization = request.headers.get("Authorization").split(" ")

        if authorization[0] == "Basic":
            authorization[1] = str(
                base64.b64decode(authorization[1]),
                "utf-8",
            ).split(
                ":"
            )[0]
        else:
            return make_exception_response("4003")

        if authorization[1] == "":
            return (
                jsonify(
                    {
                        "code": 4001,
                        "name": "NoAuthenticationInformation",
                        "message": "Server failed to authenticate the request. No authentication code was provided.",
                    }
                ),
                401,
            )

        try:
            user: User = TornKey.select(TornKey.user).where(TornKey.api_key == authorization[1]).get().user
        except DoesNotExist:
            return make_exception_response("4001")

        kwargs["user"] = user
        kwargs["key"] = authorization
        kwargs["start_time"] = start_time

        return func(*args, **kwargs)

    return wrapper


def global_cache(func=None, duration=3600):
    if not func:
        return partial(global_cache, duration=duration)

    @wraps(func)
    def wrapper(*args, **kwargs):
        # TODO: Migrate this redis call back into tornium-commons
        client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=False)

        cached_response = client.get(f"tornium:cache:{request.url_rule}")

        if cached_response is None:
            endpoint_response: typing.Tuple[Response, int, dict] = func(*args, **kwargs)

            if endpoint_response[1] // 100 != 2:
                return endpoint_response
            # TODO: Don't cache API errors
            # TODO: Add type handling as only Response type responses would have the .json attribute

            client.set(
                f"tornium:cache:{request.url_rule}",
                msgpack.dumps(endpoint_response[0].json),
                nx=True,
                ex=duration,
            )

            endpoint_response[0].headers["Cache-Control"] = f"max-age={duration}, public"
            return endpoint_response

        unpacked_response: dict = msgpack.loads(cached_response)
        cache_ttl = client.ttl(f"tornium:cache:{request.url_rule}")

        return (
            unpacked_response,
            200,
            {
                "Content-Type": "application/json",
                "Cache-Control": f"max-age={cache_ttl}, public",
            },
        )

    return wrapper
