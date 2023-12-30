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

from controllers.api.v1.decorators import ratelimit, token_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@token_required
@ratelimit
def faction_retal_channel(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        faction_tid = int(data["factiontid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1102", key)

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
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = Faction.get_by_id(faction_tid)
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)

    retal_config = guild.retal_config

    try:
        retal_config[str(faction_tid)]["channel"] = str(channel_id)
    except KeyError:
        retal_config[str(faction_tid)] = {
            "channel": str(channel_id),
            "roles": [],
        }

    Server.update(retal_config=retal_config).where(Server.sid == guild.sid).execute()

    return jsonify(guild.retal_config), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def faction_retal_roles(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        faction_tid = int(data["factiontid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1102", key)

    try:
        roles = data["roles"]
    except KeyError:
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

    retal_config = guild.retal_config

    try:
        retal_config[str(faction_tid)]["roles"] = roles
    except KeyError:
        retal_config[str(faction_tid)] = {
            "channel": 0,
            "roles": roles,
        }

    Server.update(retal_config=retal_config).where(Server.sid == guild.sid).execute()

    return jsonify(guild.retal_config), 200, api_ratelimit_response(key)
