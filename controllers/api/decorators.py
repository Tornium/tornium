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
from functools import wraps

from flask import jsonify, request
from tornium_commons import rds
from tornium_commons.models import UserModel

from controllers.api.utils import make_exception_response


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

        user = UserModel.objects(key=authorization).first()

        if user is None:
            return make_exception_response("4001")

        kwargs["user"] = user
        kwargs["key"] = authorization
        kwargs["start_time"] = start_time

        return func(*args, **kwargs)

    return wrapper


def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        if request.headers.get("Authorization") is None:
            return make_exception_response("4001")

        authorization = request.headers.get("Authorization").split(" ")

        if authorization[0] != "Token":
            return make_exception_response("4003")
        elif authorization[1] == "":
            return make_exception_response("4001")

        redis_client = rds()

        try:
            # Token is too old
            if int(time.time()) - 300 > int(redis_client.get(f"tornium:token:api:{authorization[1]}")):
                return make_exception_response("4001")

            tid = int(redis_client.get(f"tornium:token:api:{authorization[1]}:tid"))
        except TypeError:
            return make_exception_response("4001")

        user: UserModel = UserModel.objects(tid=tid).first()

        if user is None:
            return make_exception_response("4001")

        kwargs["user"] = user
        kwargs["key"] = user.key
        kwargs["start_time"] = start_time

        return func(*args, **kwargs)

    return wrapper


def authentication_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        if request.headers.get("Authorization") is None:
            return make_exception_response("4001")

        authorization = request.headers.get("Authorization").split(" ")

        if authorization[0] not in ("Token", "Basic"):
            return make_exception_response("4003")

        if authorization[0] == "Basic":
            authorization[1] = str(
                base64.b64decode(authorization[1]),
                "utf-8",
            ).split(
                ":"
            )[0]

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

        if authorization[0] == "Basic":
            user = UserModel.objects(key=authorization[1]).first()

            if user is None:
                return make_exception_response("4001")

            kwargs["user"] = user
            kwargs["key"] = authorization
            kwargs["start_time"] = start_time
        elif authorization[0] == "Token":
            redis_client = rds()

            try:
                # Token is too old
                if int(time.time()) - 300 > int(redis_client.get(f"tornium:token:api:{authorization[1]}")):
                    return make_exception_response("4001")

                tid = int(redis_client.get(f"tornium:token:api:{authorization[1]}:tid"))
            except TypeError:
                return make_exception_response("4001")

            user: UserModel = UserModel.objects(tid=tid).first()

            if user is None:
                return make_exception_response("4001")

            kwargs["user"] = user
            kwargs["key"] = user.key
            kwargs["start_time"] = start_time

        return func(*args, **kwargs)

    return wrapper
