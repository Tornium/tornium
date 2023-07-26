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
from tornium_commons.models import FactionModel, ServerModel

from controllers.api.bot.config import jsonified_server_config
from controllers.api.decorators import ratelimit, token_required
from controllers.api.utils import api_ratelimit_response, make_exception_response


@token_required
@ratelimit
def faction_setter(guildid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    factiontid = data.get("factiontid")

    if factiontid is None:
        return make_exception_response("1102", key)

    try:
        factiontid = int(factiontid)
    except (TypeError, ValueError):
        return make_exception_response("1102", key)

    guild: typing.Optional[ServerModel] = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)

    faction: typing.Optional[FactionModel] = FactionModel.objects(tid=factiontid).only("tid").first()

    if faction is None:
        return make_exception_response("1102", key)

    if request.method == "POST":
        if factiontid in guild.factions:
            return make_exception_response(
                "0000", key, details={"message": "This faction is already marked for this server."}
            )

        guild.factions.append(factiontid)
        guild.save()
    elif request.method == "DELETE":
        if factiontid not in guild.factions:
            return make_exception_response(
                "0000", key, details={"message": "This faction has not been marked for this server."}
            )

        guild.factions.remove(factiontid)
        guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
