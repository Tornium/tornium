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

import time

from flask import jsonify, request
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict
from tornium_commons.models import Faction, FactionPosition, Server

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth("faction")
@ratelimit
def get_positions(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild_id = int(request.args["guildid"])
    except (KeyError, TypeError, ValueError):
        return make_exception_response("1001", key)

    try:
        faction_tid = int(request.args["factiontid"])
    except (KeyError, TypeError, ValueError):
        return make_exception_response("1102", key)

    if guild_id != 0 and faction_tid != 0:
        if kwargs["user"].faction_id != faction_tid or not kwargs["user"].faction_aa:
            try:
                guild: Server = Server.get_by_id(guild_id)
            except DoesNotExist:
                return make_exception_response("1001", key)

            if kwargs["user"].tid not in guild.admins:
                return make_exception_response("4020", key)
            elif faction_tid not in guild.factions:
                return make_exception_response("1102", key)

            try:
                faction: Faction = Faction.get_by_id(faction_tid)
            except DoesNotExist:
                return make_exception_response("1102", key)

            if faction.guild_id != guild_id:
                return make_exception_response("1102", key)
        else:
            faction: Faction = kwargs["user"].faction
    else:
        if kwargs["user"].faction is None:
            return make_exception_response("1102", key)
        elif not kwargs["user"].faction_aa:
            return make_exception_response("4005", key)

        faction: Faction = kwargs["user"].faction

    if faction is None:
        return make_exception_response("1102", key)
    elif int(time.time()) - faction.last_members.timestamp() >= 86400:  # one day
        return make_exception_response(
            "0000",
            key,
            details={"message": "The data hasn't been updated sufficiently recently."},
        )

    positions = FactionPosition.select().where(FactionPosition.faction_tid == faction_tid)

    if positions.count() == 0:
        return make_exception_response("1103", key)

    positions_data = []

    position: FactionPosition
    for position in positions:
        position_data = model_to_dict(position)
        position_data["_id"] = str(position.pid)
        positions_data.append(position_data)

    return jsonify({"positions": positions_data}), 200, api_ratelimit_response(key)
