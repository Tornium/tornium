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
import typing

from flask import request
from peewee import DoesNotExist
from tornium_commons import rds
from tornium_commons.models import Faction, Server

from controllers.api.bot.config import jsonified_server_config
from controllers.api.decorators import ratelimit, token_required
from controllers.api.utils import api_ratelimit_response, make_exception_response


@token_required
@ratelimit
def armory_tracked_items(guildid: int, factionid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        item_id = int(data["item"])
    except (TypeError, ValueError, KeyError):
        return make_exception_response("1104", key)

    try:
        quantity = int(data["quantity"])
    except (TypeError, ValueError, KeyError):
        if request.method == "POST":  # Only necessary for new tracked items
            return make_exception_response("1000", key, details={"element": "quantity"})

    if not rds().hexists("tornium:items:name-map", item_id):
        return make_exception_response("1104", key)

    try:
        guild: Server = Server.get_by_id(guildid)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif factionid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = Faction.get_by_id(factionid)
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)

    if request.method == "DELETE":
        try:
            del guild.armory_config[str(factionid)]["items"][str(item_id)]
        except KeyError:
            return make_exception_response("1000", key)
    elif request.method == "POST":
        try:
            guild.armory_config[str(factionid)]["items"][str(item_id)] = quantity
        except KeyError:
            guild.armory_config[str(factionid)] = {
                "enabled": False,
                "channel": 0,
                "roles": [],
                "items": {
                    str(item_id): quantity,
                },
            }

    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def armorer_roles(guildid: int, factionid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles: typing.Optional[typing.Iterable[str]] = data.get("roles")

    try:
        guild: Server = Server.get_by_id(guildid)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif factionid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = Faction.get_by_id(factionid)
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)

    try:
        guild.armory_config[str(factionid)]["roles"] = roles
    except KeyError:
        guild.armory_config[str(factionid)] = {
            "enabled": False,
            "channel": 0,
            "roles": roles,
            "items": {},
        }

    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def armory_channel(guildid: int, factionid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    channel: typing.Optional[str] = data.get("channel")

    if channel in ("", None) or (isinstance(channel, str) and not channel.isdigit()):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.get_by_id(guildid)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif factionid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = Faction.get_by_id(factionid)
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)

    try:
        guild.armory_config[str(factionid)]["channel"] = channel
    except KeyError:
        guild.armory_config[str(factionid)] = {
            "enabled": False,
            "channel": channel,
            "roles": [],
            "items": {},
        }

    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def armory_toggle(guildid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    enabled: typing.Optional[bool] = data.get("enabled")

    if enabled is None or not isinstance(enabled, bool):
        return make_exception_response("1000", key, details={"element": "enabled"})

    try:
        guild: Server = Server.get_by_id(guildid)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif kwargs["user"].faction.tid not in guild.factions:
        return make_exception_response("4021", key)

    if guild.sid != kwargs["user"].faction.guild_id:
        return make_exception_response("4021", key)

    if guild.armory_enabled == enabled:
        return make_exception_response("1000", key, details={"message": "Invalid enabled state"})

    guild.armory_enabled = enabled
    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def armory_faction_toggle(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    enabled: typing.Optional[bool] = data.get("enabled")

    if enabled is None or not isinstance(enabled, bool):
        return make_exception_response("1000", key, details={"element": "enabled"})

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

    if str(faction_tid) in guild.armory_config and guild.armory_config.get("enabled") == enabled:
        return make_exception_response("1000", key, details={"message": "Invalid enabled state"})

    try:
        guild.armory_config[str(faction_tid)]["enabled"] = enabled
    except KeyError:
        guild.armory_config[str(faction_tid)] = {
            "enabled": enabled,
            "channel": 0,
            "roles": [],
            "items": {},
        }

    guild.save()
    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
