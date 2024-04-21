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
import logging
import typing

from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2.rfc6749 import InvalidScopeError, OAuth2Error
from flask import jsonify, request
from peewee import DoesNotExist
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.formatters import bs_to_range
from tornium_commons.models import Stat, User

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response
from estimate import estimate_user


@require_oauth("identity")
@ratelimit
def get_user(*args, **kwargs):
    return (
        jsonify(
            {
                "tid": kwargs["user"].tid,
                "name": kwargs["user"].name,
                "username": f'{kwargs["user"].name} [{kwargs["user"].tid}]',
                "last_refresh": kwargs["user"].last_refresh.timestamp(),
                "battlescore": kwargs["user"].battlescore,
                "battlescore_update": kwargs["user"].battlescore_update.timestamp(),
                "discord_id": kwargs["user"].discord_id,
                "factiontid": kwargs["user"].faction_id,
                "aa": kwargs["user"].faction_aa,
                "status": kwargs["user"].status,
                "last_action": kwargs["user"].last_action.timestamp(),
            }
        ),
        200,
        api_ratelimit_response(f'tornium:ratelimit:{kwargs["user"].tid}'),
    )


@require_oauth()
@ratelimit
def get_specific_user(tid: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    refresh: typing.Union[str, bool] = request.args.get("refresh", False)

    if isinstance(refresh, str):
        if refresh.lower() == "true":
            refresh = True
        elif refresh.lower() == "false":
            refresh = False
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Invalid refresh type",
                },
            )

    try:
        if refresh and require_oauth.validate_request("torn_key:usage", request):
            return require_oauth.raise_error_response(InvalidScopeError())
    except OAuth2Error as e:
        return require_oauth.raise_error_response(e)

    if refresh:
        update_user(kwargs["user"].key, tid=tid, refresh_existing=True)

    try:
        user: User = User.get_by_id(tid)
    except DoesNotExist:
        return make_exception_response("1100", key)

    return (
        jsonify(
            {
                "tid": user.tid,
                "name": user.name,
                "username": f"{user.name} [{user.tid}]",
                "level": user.level,
                "last_refresh": user.last_refresh.timestamp(),
                "discord_id": user.discord_id,
                "faction": {"tid": user.faction_id, "name": user.faction.name} if user.faction is not None else None,
                "status": user.status,
                "last_action": user.last_action.timestamp(),
            }
        ),
        200,
        api_ratelimit_response(key),
    )


@require_oauth(["", "torn_key:usage"])
@ratelimit
def estimate_specific_user(tid: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    estimate_ratelimit = f"tornium:estimate:ratelimit:{kwargs['user'].tid}"
    redis_client = rds()

    if not redis_client.set(estimate_ratelimit, 25, nx=True, ex=60 - datetime.datetime.utcnow().second):
        # Ratelimit just created in redis
        try:
            if int(redis_client.get(estimate_ratelimit)) > 0:
                redis_client.decrby(estimate_ratelimit, 1)
            else:
                return make_exception_response("4293", key)
        except TypeError:
            redis_client.set(estimate_ratelimit, 10, ex=60 - datetime.datetime.utcnow().second)

    try:
        estimated_bs, expiration_ts = estimate_user(
            tid,
            kwargs["user"].key,
            allow_api_calls="torn_key:usage" in current_token.get_scope() and kwargs["user"].key not in ("", None),
        )
    except ValueError as e:
        logging.getLogger("server").exception(e)
        return make_exception_response("1100", key)
    except PermissionError:
        return require_oauth.raise_error_response(InvalidScopeError())

    min_bs, max_bs = bs_to_range(estimated_bs)

    return (
        {
            "min_bs": min_bs,
            "max_bs": max_bs,
            "expiration": expiration_ts,
        },
        200,
        api_ratelimit_response(key),
    )


@require_oauth()
@ratelimit
def latest_user_stats(tid: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if kwargs["user"].faction is not None:
        stat: typing.Optional[Stat] = (
            Stat.select(Stat.battlescore, Stat.time_added)
            .where((Stat.tid == tid) & ((Stat.added_group == 0) | (Stat.added_group == kwargs["user"].faction_id)))
            .order_by(-Stat.time_added)
            .first()
        )
    else:
        stat: typing.Optional[Stat] = (
            Stat.select(Stat.battlescore, Stat.time_added)
            .where((Stat.tid == tid) & (Stat.added_group == 0))
            .order_by(-Stat.time_added)
            .first()
        )

    if stat is None:
        return make_exception_response("1100", key)

    min_bs, max_bs = bs_to_range(stat.battlescore)

    return (
        {
            "min": min_bs,
            "max": max_bs,
            "timestamp": stat.time_added.timestamp(),
        },
        200,
        api_ratelimit_response(key),
    )
