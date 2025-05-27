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

import time
import typing
from functools import partial, wraps

import redis
from authlib.integrations.flask_oauth2 import current_token
from flask import Response, request, session
from flask_login import current_user
from tornium_commons import rds
from tornium_commons.altjson import loads, dumps
from tornium_commons.oauth import BearerTokenValidator, ResourceProtector

from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


def ratelimit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # OAuth token
            kwargs["user"] = current_token.user
            kwargs["key"] = current_token.user.key
        except AttributeError:
            # CSRF token
            kwargs["user"] = current_user
            kwargs["key"] = current_user.key

        client = rds()
        key = f"tornium:ratelimit:{kwargs['user'].tid}"

        current_count = int(client.incr(key))

        if current_count <= 1:
            client.expireat(key, int(time.time()) // 60 * 60 + 60)
        elif current_count > 250:
            return make_exception_response("4000", key)

        return func(*args, **kwargs)

    return wrapper


def session_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return make_exception_response("4001")

        csrf_token = request.headers.get("X-CSRF-Token") or request.headers.get("CSRF-Token")

        if csrf_token != session.get("csrf_token") and csrf_token is not None:
            return make_exception_response("4002")

        kwargs["user"] = current_user
        kwargs["key"] = current_user.key

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
                dumps(endpoint_response[0].json),
                nx=True,
                ex=duration,
            )

            endpoint_response[0].headers["Cache-Control"] = f"max-age={duration}, public"
            return endpoint_response

        unpacked_response: dict = loads(cached_response)
        cache_ttl = client.ttl(f"tornium:cache:{request.url_rule}")

        return (
            unpacked_response,
            200,
            {
                "Content-Type": "application/json",
                "Cache-Control": f"max-age={cache_ttl}, public",
                **api_ratelimit_response(f"tornium:ratelimit:{kwargs['user'].tid}", client),
            },
        )

    return wrapper


require_oauth = ResourceProtector()
require_oauth.register_token_validator(BearerTokenValidator())
