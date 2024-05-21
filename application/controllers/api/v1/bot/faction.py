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
from tornium_commons.models import Faction, Server

from controllers.api.v1.bot.config import jsonified_server_config
from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def faction_setter(guild_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        faction_tid = int(data["factiontid"])
    except (KeyError, TypeError, ValueError):
        return make_exception_response("1102", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    try:
        Faction.select().where(Faction.tid == faction_tid).get()
    except DoesNotExist:
        return make_exception_response("1102", key)

    if request.method == "POST":
        if faction_tid in guild.factions:
            return make_exception_response(
                "0000",
                key,
                details={"message": "This faction is already marked for this server."},
            )

        guild.factions.append(faction_tid)
        Server.update(factions=guild.factions).where(Server.sid == guild.sid).execute()
    elif request.method == "DELETE":
        if faction_tid not in guild.factions:
            return make_exception_response(
                "0000",
                key,
                details={"message": "This faction has not been marked for this server."},
            )

        guild.factions.remove(faction_tid)
        Server.update(factions=guild.factions).where(Server.sid == guild.sid).execute()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
