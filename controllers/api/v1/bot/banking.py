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
from peewee import DoesNotExist
from tornium_commons.models import Faction, Server

from controllers.api.v1.bot.config import jsonified_server_config
from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def banking_setter(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    channel_id = data.get("channel")
    roles_id = data.get("roles")

    if channel_id is None and roles_id is None:
        return make_exception_response("1000", key)
    elif channel_id is not None and (channel_id in ("", 0) or not channel_id.isdigit()):
        return make_exception_response("1002", key)
    elif roles_id is not None and not isinstance(roles_id, list):
        return make_exception_response("1003", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = Faction.get_by_id(faction_tid)
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)

    banking_config = guild.banking_config.get(
        str(faction.tid),
        {
            "channel": "0",
            "roles": [],
        },
    )

    if channel_id is not None:
        banking_config["channel"] = channel_id

    if roles_id is not None:
        try:
            banking_config["roles"] = list(set(map(str, roles_id)))
        except TypeError:
            return make_exception_response("1003", key)

    guild.banking_config[str(faction.tid)] = banking_config

    Server.update(banking_config=guild.banking_config).where(Server.sid == guild.sid).execute()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def banking_getter(guild_id: int, faction_tid: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = Faction.get_by_id(faction_tid)
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)

    banking_config = guild.banking_config.get(
        str(faction.tid),
        {
            "channel": "0",
            "roles": [],
        },
    )

    return (
        jsonify(
            {
                "channel": banking_config["channel"],
                "roles": banking_config["roles"],
            }
        ),
        200,
        api_ratelimit_response(key),
    )
