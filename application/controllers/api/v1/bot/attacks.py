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
from tornium_commons.models import Faction, Server, ServerAttackConfig

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


def _update_attack_config(faction_tid: int, server_sid: int, **kwargs):
    ServerAttackConfig.insert(
        faction=faction_tid,
        server=server_sid,
        **kwargs,
    ).on_conflict(
        conflict_target=[ServerAttackConfig.faction, ServerAttackConfig.server],
        preserve=[getattr(ServerAttackConfig, k) for k in kwargs.keys()],
    ).execute()


@session_required
@ratelimit
def faction_retal_channel(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        channel_id = int(data["channel"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.select(Server.admins, Server.factions).where(Server.sid == guild_id).get()
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

    if guild_id != faction.guild_id:
        return make_exception_response("4021", key)

    _update_attack_config(faction_tid, guild_id, retal_channel=channel_id)

    return "", 204, api_ratelimit_response(key)


@session_required
@ratelimit
def faction_retal_roles(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        roles = list(map(int, data["roles"]))
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1003", key)

    try:
        guild: Server = Server.select(Server.admins, Server.factions).where(Server.sid == guild_id).get()
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

    if guild_id != faction.guild_id:
        return make_exception_response("4021", key)

    _update_attack_config(faction_tid, guild_id, retal_roles=roles)

    return "", 204, api_ratelimit_response(key)


@session_required
@ratelimit
def faction_chain_bonus_channel(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        channel_id = int(data["channel"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.select(Server.admins, Server.factions).where(Server.sid == guild_id).get()
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

    if guild_id != faction.guild_id:
        return make_exception_response("4021", key)

    _update_attack_config(faction_tid, guild_id, chain_bonus_channel=channel_id)

    return "", 204, api_ratelimit_response(key)


@session_required
@ratelimit
def faction_chain_bonus_roles(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        roles = list(map(int, data["roles"]))
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1003", key)

    try:
        guild: Server = Server.select(Server.admins, Server.factions).where(Server.sid == guild_id).get()
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

    if guild_id != faction.guild_id:
        return make_exception_response("4021", key)

    _update_attack_config(faction_tid, guild_id, chain_bonus_roles=roles)

    return "", 204, api_ratelimit_response(key)


@session_required
@ratelimit
def faction_chain_bonus_length(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        length = int(data["length"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("0", key, details={"message": "Invalid chain length"})

    try:
        guild: Server = Server.select(Server.admins, Server.factions).where(Server.sid == guild_id).get()
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

    if guild_id != faction.guild_id:
        return make_exception_response("4021", key)

    _update_attack_config(faction_tid, guild_id, chain_bonus_length=length)

    return "", 204, api_ratelimit_response(key)


@session_required
@ratelimit
def faction_chain_alert_channel(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        channel_id = int(data["channel"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.select(Server.admins, Server.factions).where(Server.sid == guild_id).get()
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

    if guild_id != faction.guild_id:
        return make_exception_response("4021", key)

    _update_attack_config(faction_tid, guild_id, chain_alert_channel=channel_id)

    return "", 204, api_ratelimit_response(key)


@session_required
@ratelimit
def faction_chain_alert_roles(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        roles = list(map(int, data["roles"]))
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1003", key)

    try:
        guild: Server = Server.select(Server.admins, Server.factions).where(Server.sid == guild_id).get()
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

    if guild_id != faction.guild_id:
        return make_exception_response("4021", key)

    _update_attack_config(faction_tid, guild_id, chain_alert_roles=roles)

    return "", 204, api_ratelimit_response(key)
