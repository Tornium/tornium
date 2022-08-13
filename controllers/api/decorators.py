# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import base64
import datetime
from functools import wraps, partial
import time

from flask import jsonify, request

from models.keymodel import KeyModel
from models.usermodel import UserModel
import redisdb
import utils


def ratelimit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        client = redisdb.get_redis()
        key = f'tornium:ratelimit:{kwargs["user"].tid}'
        limit = 250 if kwargs["user"].pro else 150

        if client.setnx(key, limit):
            client.expire(key, 60 - datetime.datetime.utcnow().second)

        value = client.get(key)

        if client.ttl(key) < 0:
            client.expire(key, 1)

        if value and int(value) > 0:
            client.decrby(key, 1)
        else:
            return (
                jsonify(
                    {
                        "code": 4000,
                        "name": "Too Many Requests",
                        "message": "Server failed to respond to request. Too many requests were received.",
                    }
                ),
                429,
                {
                    "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )

        return func(*args, **kwargs)

    return wrapper


def requires_scopes(func=None, scopes=None):
    if not func:
        return partial(requires_scopes, scopes=scopes)

    @wraps(func)
    def wrapper(*args, **kwargs):
        client = redisdb.get_redis()
        key = f'tornium:ratelimit:{kwargs["user"].tid}'

        if (
            kwargs["keytype"] == "Tornium"
            and not set(KeyModel.objects(key=kwargs["key"]).first().scopes) & scopes
        ):
            return (
                jsonify(
                    {
                        "code": 4004,
                        "name": "InsufficientPermissions",
                        "message": "Server failed to fulfill the request. The scope of the Tornium key provided was not "
                        "sufficient for the request.",
                    }
                ),
                403,
                {
                    "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )

        return func(*args, **kwargs)

    return wrapper


def torn_key_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        if request.headers.get("Authorization") is None:
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
        elif request.headers.get("Authorization").split(" ")[0] != "Basic":
            return (
                jsonify(
                    {
                        "code": 4003,
                        "name": "InvalidAuthenticationType",
                        "message": "Server failed to authenticate the request. The provided authentication type was not "
                        '"Basic" and therefore invalid.',
                    }
                ),
                401,
            )

        authorization = str(
            base64.b64decode(request.headers.get("Authorization").split(" ")[1]),
            "utf-8",
        ).split(":")[0]

        if authorization == "":
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

        user = UserModel.objects(key=authorization).first()

        if user is None:
            return (
                jsonify(
                    {
                        "code": 4001,
                        "name": "InvalidAuthenticationInformation",
                        "message": "Server failed to authenticate the request. The provided authentication code was invalid.",
                    }
                ),
                401,
            )

        kwargs["user"] = user
        kwargs["keytype"] = "Torn"
        kwargs["key"] = authorization
        kwargs["start_time"] = start_time

        return func(*args, **kwargs)

    return wrapper


def tornium_key_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        if request.headers.get("Authorization") is None:
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
        elif request.headers.get("Authorization").split(" ")[0] != "Basic":
            return (
                jsonify(
                    {
                        "code": 4003,
                        "name": "InvalidAuthenticationType",
                        "message": "Server failed to authenticate the request. The provided authentication type was not "
                        '"Basic" and therefore invalid.',
                    }
                ),
                401,
            )

        authorization = str(
            base64.b64decode(request.headers.get("Authorization").split(" ")[1]),
            "utf-8",
        ).split(":")[0]

        if authorization == "":
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

        key = KeyModel.objects(key=authorization).first()

        if key is None:
            return (
                jsonify(
                    {
                        "code": 4001,
                        "name": "InvalidAuthenticationInformation",
                        "message": "Server failed to authenticate the request. The provided authentication code was invalid.",
                    }
                ),
                401,
            )

        kwargs["user"] = UserModel.objects(tid=key.ownertid).first()
        kwargs["keytype"] = "Tornium"
        kwargs["key"] = authorization
        kwargs["start_time"] = start_time

        return func(*args, **kwargs)

    return wrapper


def key_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        if request.headers.get("Authorization") is None:
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
        elif request.headers.get("Authorization").split(" ")[0] != "Basic":
            return (
                jsonify(
                    {
                        "code": 4003,
                        "name": "InvalidAuthenticationType",
                        "message": "Server failed to authenticate the request. The provided authentication type was not "
                        '"Basic" and therefore invalid.',
                    }
                ),
                401,
            )

        authorization = str(
            base64.b64decode(request.headers.get("Authorization").split(" ")[1]),
            "utf-8",
        ).split(":")[0]

        if authorization == "":
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

        key = KeyModel.objects(key=authorization).first()
        user = UserModel.objects(key=authorization).first()

        if user is not None:
            kwargs["user"] = user
            kwargs["keytype"] = "Torn"
            kwargs["key"] = authorization
            kwargs["start_time"] = start_time
        elif key is not None:
            kwargs["user"] = UserModel.objects(tid=key.ownertid).first()
            kwargs["keytype"] = "Tornium"
            kwargs["key"] = authorization
            kwargs["start_time"] = start_time
        else:
            return (
                jsonify(
                    {
                        "code": 4001,
                        "name": "InvalidAuthenticationInformation",
                        "message": "Server failed to authenticate the request. The provided authentication code was invalid.",
                    }
                ),
                401,
            )

        return func(*args, **kwargs)

    return wrapper


def pro_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not kwargs["user"].pro:
            client = redisdb.get_redis()
            key = f'tornium:ratelimit:{kwargs["user"].tid}'

            return (
                jsonify(
                    {
                        "code": 4011,
                        "name": "InsufficientUserType",
                        "message": "Server failed to fulfill the request. The provided authentication code was not sufficient "
                        "for a pro level request.",
                    }
                ),
                402,
                {
                    "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )

        return func(*args, **kwargs)

    return wrapper
