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
from tornium_commons.models import FactionModel, ServerModel

from controllers.api.decorators import authentication_required, ratelimit
from controllers.api.utils import api_ratelimit_response, make_exception_response


@authentication_required
@ratelimit
def faction_retal_channel(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = data.get("guildid")
    factiontid = data.get("factiontid")
    channelid = data.get("channel")

    if guildid in ("", None, 0) or not guildid.isdigit():
        return make_exception_response("1001", key)
    elif factiontid in ("", None, 0) or not factiontid.isdigit():
        return make_exception_response("1102", key)
    elif channelid in ("", None) or not channelid.isdigit():
        return make_exception_response("1002", key)

    guildid = int(guildid)
    factiontid = int(factiontid)
    channelid = int(channelid)

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif factiontid not in guild.factions:
        return make_exception_response("4021", key)

    faction: FactionModel = FactionModel.objects(tid=factiontid).first()

    if faction is None or faction.guild != guildid:
        return make_exception_response("1102", key)

    try:
        guild.retal_config[str(factiontid)]["channel"] = str(channelid)
    except KeyError:
        guild.retal_config[str(factiontid)] = {
            "channel": str(channelid),
            "roles": [],
        }

    guild.save()

    return (jsonify(guild.retal_config), 200, api_ratelimit_response(key))


@authentication_required
@ratelimit
def faction_retal_roles(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = data.get("guildid")
    factiontid = data.get("factiontid")
    roles = data.get("roles")

    if guildid in ("", None, 0) or not guildid.isdigit():
        return make_exception_response("1001", key)
    elif factiontid in ("", None, 0) or not factiontid.isdigit():
        return make_exception_response("1102", key)
    elif roles is None:
        return make_exception_response("1003", key)

    guildid = int(guildid)
    factiontid = int(factiontid)

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif factiontid not in guild.factions:
        return make_exception_response("4021", key)

    faction: FactionModel = FactionModel.objects(tid=factiontid).first()

    if faction is None or faction.guild != guildid:
        return make_exception_response("1102", key)

    try:
        guild.retal_config[str(factiontid)]["roles"] = roles
    except KeyError:
        guild.retal_config[str(factiontid)] = {
            "channel": 0,
            "roles": roles,
        }

    guild.save()

    return (jsonify(guild.retal_config), 200, api_ratelimit_response(key))
