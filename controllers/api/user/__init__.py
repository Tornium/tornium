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
import typing

from flask import jsonify, request
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.formatters import bs_to_range
from tornium_commons.models import FactionModel, UserModel

from controllers.api.decorators import authentication_required, ratelimit
from controllers.api.utils import api_ratelimit_response, make_exception_response
from estimate import estimate_user


@authentication_required
@ratelimit
def get_user(*args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    return (
        jsonify(
            {
                "tid": kwargs["user"].tid,
                "name": kwargs["user"].name,
                "username": f'{kwargs["user"].name} [{kwargs["user"].tid}]',
                "last_refresh": kwargs["user"].last_refresh,
                "battlescore": kwargs["user"].battlescore,
                "battlescore_update": kwargs["user"].battlescore_update,
                "discord_id": kwargs["user"].discord_id,
                "factiontid": kwargs["user"].factionid,
                "aa": kwargs["user"].factionaa,
                "status": kwargs["user"].status,
                "last_action": kwargs["user"].last_action,
            }
        ),
        200,
        api_ratelimit_response(key),
    )


@authentication_required
@ratelimit
def get_specific_user(tid: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    refresh: typing.Union[str, bool] = request.args.get("refresh", False)

    if type(refresh) == str:
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

    if refresh:
        update_user(kwargs["user"].key, tid=tid, refresh_existing=True)

    user: typing.Optional[UserModel] = UserModel.objects(tid=tid).no_cache().first()

    if user is None:
        return make_exception_response("1100", key)

    faction: typing.Optional[FactionModel] = (
        None if user.factionid == 0 else FactionModel.objects(tid=user.factionid).first()
    )

    return (
        jsonify(
            {
                "tid": user.tid,
                "name": user.name,
                "username": f"{user.name} [{user.tid}]",
                "level": user.level,
                "last_refresh": user.last_refresh,
                "discord_id": user.discord_id,
                "faction": {"tid": user.factionid, "name": faction.name} if faction is not None else None,
                "status": user.status,
                "last_action": user.last_action,
            }
        ),
        200,
        api_ratelimit_response(key),
    )


@authentication_required
@ratelimit
def estimate_single_user(tid: int, *args, **kwargs):
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

    estimated_bs, expiration_ts = estimate_user(tid, kwargs["user"].key)
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
