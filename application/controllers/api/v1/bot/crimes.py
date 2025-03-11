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

import peewee
from flask import request
from peewee import DoesNotExist
from tornium_commons.models import Faction, OrganizedCrimeNew, Server, ServerOCConfig

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def set_tool_channel(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    channel_id = data.get("channel")

    if channel_id is None:
        return make_exception_response("1002", key)
    elif channel_id is not None and (channel_id in ("", 0) or not channel_id.isdigit()):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, tool_channel=channel_id)

    return oc_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_tool_roles(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None:
        return make_exception_response("1002", key)
    elif roles is not None and not isinstance(roles, list):
        return make_exception_response("1003", key)

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, tool_roles=list(set(map(int, roles))))

    return oc_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_tool_crimes(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    crimes = data.get("crimes")

    if crimes is None:
        return make_exception_response("1002", key)
    elif crimes is not None and not isinstance(crimes, list):
        return make_exception_response("1003", key)

    db_oc_names = [crime.oc_name for crime in OrganizedCrimeNew.select().distinct(OrganizedCrimeNew.oc_name)]
    if len(set(crimes) - set(db_oc_names)) != 0:
        # At least one invalid OC name
        return make_exception_response("1105", key)

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, tool_crimes=list(set(crimes)))

    return oc_config.to_dict(), 200, api_ratelimit_response(key)
