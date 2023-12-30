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
def assists_channel(guildid, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    channel_id = data.get("channel")

    if guildid in ("", None, 0) or (type(guildid) != int and not guildid.isdigit()):
        return make_exception_response("1001", key)
    elif channel_id in ("", None, 0) or (type(channel_id) != int and not channel_id.isdigit()):
        return make_exception_response("1002", key)

    channel_id = int(channel_id)

    try:
        guild: Server = Server.get_by_id(guildid)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    Server.update(assist_channel=channel_id).where(Server.sid == guild.sid).execute()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def assists_role_set(guild_id: int, role_type: str, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if role_type not in ["smoker", "tear", "l0", "l1", "l2", "l3"]:
        return make_exception_response("1000", key, details={"element": "role_type"})

    roles = data.get("roles")

    if type(roles) != list:
        return make_exception_response("1000", key, details={"element": "roles"})

    try:
        roles = [int(r) for r in roles]
    except ValueError:
        return make_exception_response("1000", key, details={"element": "roles"})

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    if role_type == "smoker":
        Server.update(assist_smoker_roles=roles).where(Server.sid == guild.sid).execute()
    elif role_type == "tear":
        Server.update(assist_tear_roles=roles).where(Server.sid == guild.sid).execute()
    elif role_type == "l0":
        Server.update(assist_l0_roles=roles).where(Server.sid == guild.sid).execute()
    elif role_type == "l1":
        Server.update(assist_l1_roles=roles).where(Server.sid == guild.sid).execute()
    elif role_type == "l2":
        Server.update(assist_l2_roles=roles).where(Server.sid == guild.sid).execute()
    elif role_type == "l3":
        Server.update(assist_l3_roles=roles).where(Server.sid == guild.sid).execute()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
