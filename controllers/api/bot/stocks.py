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

import json

from flask import request
from peewee import DoesNotExist
from tornium_commons.models import Server

from controllers.api.bot.config import jsonified_server_config
from controllers.api.decorators import ratelimit, token_required
from controllers.api.utils import api_ratelimit_response, make_exception_response


@token_required
@ratelimit
def stocks_feed_channel(guild_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        channel_id = int(data["channel"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    Server.update(stocks_channel=channel_id).where(Server.sid == guild.sid).execute()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def stocks_feed_options(guild_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    percent_change = data.get("percent_change")
    cap_change = data.get("cap_change")
    new_day_price = data.get("new_day_price")
    min_price = data.get("min_price")
    max_price = data.get("max_price")

    if type(percent_change) not in (bool, None):
        return make_exception_response("0000", key, details={"key": "percent_change"})
    elif type(cap_change) not in (bool, None):
        return make_exception_response("0000", key, details={"key": "cap_change"})
    elif type(new_day_price) not in (bool, None):
        return make_exception_response("0000", key, details={"key": "new_day_price"})
    elif type(min_price) not in (bool, None):
        return make_exception_response("0000", key, details={"key": "min_price"})
    elif type(max_price) not in (bool, None):
        return make_exception_response("0000", key, details={"key": "max_price"})

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    if percent_change is not None:
        guild.stocks_config["percent_change"] = bool(percent_change)
    if cap_change is not None:
        guild.stocks_config["cap_change"] = bool(cap_change)
    if new_day_price is not None:
        guild.stocks_config["new_day_price"] = bool(new_day_price)
    if min_price is not None:
        guild.stocks_config["min_price"] = bool(min_price)
    if max_price is not None:
        guild.stocks_config["max_price"] = bool(max_price)

    Server.update(stocks_config=guild.stocks_config).where(Server.sid == guild.sid).execute()
    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
