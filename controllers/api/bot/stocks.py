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

from flask import jsonify, request
from tornium_commons.models import ServerModel

from controllers.api.bot.config import jsonified_server_config
from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def stocks_feed_channel(guildid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    channel_id = data.get("channel")

    if channel_id in ("", 0, None) or not channel_id.isdigit():
        return make_exception_response("1002", key)

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    guild.stocks_channel = channel_id
    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def stocks_feed_options(guildid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    percent_change = data.get("percent_change")
    cap_change = data.get("cap_change")
    new_day_price = data.get("new_day_price")
    min_price = data.get("min_price")
    max_price = data.get("max_price")

    if type(percent_change) not in (bool, None):
        return make_exception_response("0", key, details={"key": "percent_change"})
    elif type(cap_change) not in (bool, None):
        return make_exception_response("0", key, details={"key": "cap_change"})
    elif type(new_day_price) not in (bool, None):
        return make_exception_response("0", key, details={"key": "new_day_price"})
    elif type(min_price) not in (bool, None):
        return make_exception_response("0", key, details={"key": "min_price"})
    elif type(max_price) not in (bool, None):
        return make_exception_response("0", key, details={"key": "max_price"})

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif kwargs["user"].tid not in guild.admins:
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

    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
