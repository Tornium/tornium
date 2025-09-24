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

import json

from flask import request
from peewee import DoesNotExist
from tornium_commons.models import Faction, Server, ServerOverdoseConfig

from controllers.api.v1.bot.config import jsonified_server_config
from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def set_overdose_channel(guild_id: int, faction_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    channel_id = data.get("channel")

    if channel_id == "0" or channel_id == 0:
        channel_id = None
    if channel_id is not None and (channel_id in ("", 0) or not channel_id.isdigit()):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_id not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = Faction.select(Faction.guild).where(Faction.tid == faction_id).get()
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)

    ServerOverdoseConfig.create_or_update(guild_id, faction_id, channel=channel_id)

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_overdose_policy(guild_id: int, faction_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    policy = data.get("policy")

    if policy not in ("immediate", "daily"):
        return make_exception_response("1000", key)

    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_id not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = Faction.select(Faction.guild).where(Faction.tid == faction_id).get()
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)

    ServerOverdoseConfig.create_or_update(guild_id, faction_id, policy=policy)

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
