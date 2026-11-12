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

from authlib.integrations.flask_oauth2 import current_token
from flask import Response, request, session
from flask_login import current_user
from tornium_commons import rds
from tornium_commons.altjson import dumps, loads
from tornium_commons.models import OAuthToken
from tornium_commons.oauth import BearerTokenValidator, ResourceProtector

from controllers.api.v1.utils import api_ratelimit_response, make_exception_response

API_ACCESS_METHODS = ("oauth_client_credentials", "oauth", "session")
API_MAX_RATELIMITS = {"oauth_client_credentials": 100, "oauth": 250, "session": 250}


def allow_resource_tokens(func):
    """
    Mark an API endpoint as accepting requests from OAuth clients using client credential
    grant with consent from the applicable resource.
    """

    func.allow_resource_tokens = True
    return func


def ratelimit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if isinstance(current_token, OAuthToken) and current_token.client.check_grant_type("client_credentials"):
            # As this OAuth token is of the client credentials grant, we need to check
            # if this API endpoint allows these tokens to access it.
            if not getattr(func, "allow_resource_tokens", False):
                return make_exception_response(
                    "4004", details={"message": "This API endpoint does not support client credentials grant."}
                )

            ratelimiting_key = f"tornium:ratelimit:client:{current_token.client_id}"
            access_method = "oauth_client_credentials"

            kwargs["user"] = None
            kwargs["key"] = None
        elif isinstance(current_token, OAuthToken):
            ratelimiting_key = f"tornium:ratelimit:{current_token.user.tid}"
            access_method = "oauth"

            kwargs["user"] = current_token.user
            kwargs["key"] = current_token.user.key
        else:
            ratelimiting_key = f"tornium:ratelimit:{current_user.tid}"
            access_method = "session"

            kwargs["user"] = current_user
            kwargs["key"] = current_user.key

        # We need to provide the ratelimiting key so that API endpoints can use the correct
        # key when returning data. Otherwise, when using client credentials grant, it'll
        # provide inaccurate data.
        kwargs["ratelimiting_key"] = ratelimiting_key
        kwargs["method"] = access_method

        client = rds()
        current_count = int(client.incr(ratelimiting_key))
        client.expireat(ratelimiting_key, int(time.time()) // 60 * 60 + 60)

        if current_count > API_MAX_RATELIMITS[access_method]:
            return make_exception_response("4000", ratelimiting_key)

        return func(*args, **kwargs)

    return wrapper


def scoped_ratelimit(scope, maximum):
    """
    A scoped ratelimiting decorator.

    The `scope` is either a string or a lambda function. The lambda function will take the authenticated user
    as the argument. The `maximum` is the maximum number of API calls to this scope per minute.
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if isinstance(scope, str):
                key = scope
            elif isinstance(scope, typing.Callable):
                key = scope(kwargs["user"])
            else:
                raise Exception("Invalid scope type")

            client = rds()
            current_count = int(client.incr(key))
            client.expireat(key, int(time.time()) // 60 * 60 + 60)

            if current_count > maximum:
                return make_exception_response("4000", key, details={"scope": key})

            return f(*args, **kwargs)

        return wrapper

    return decorator


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
        client = rds()

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
            endpoint_response[0].headers["X-Cache"] = "MISS"
            return endpoint_response

        unpacked_response: dict = loads(cached_response)
        cache_ttl = client.ttl(f"tornium:cache:{request.url_rule}")

        return (
            unpacked_response,
            200,
            {
                "Content-Type": "application/json",
                "Cache-Control": f"max-age={cache_ttl}, public",
                "X-Cache": "HIT",
                **api_ratelimit_response(f"tornium:ratelimit:{kwargs['user'].tid}", client),
            },
        )

    return wrapper


require_oauth = ResourceProtector()
require_oauth.register_token_validator(BearerTokenValidator())
