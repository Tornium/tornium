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

import utils
from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.factionmodel import FactionModel
from models.positionmodel import PositionModel
from models.servermodel import ServerModel


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:faction", "faction:admin"})
def get_positions(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = request.args.get("guildid")
    factiontid = request.args.get("factiontid")

    if guildid not in (None, 0, "") and factiontid not in (None, 0, "") and guildid.isdigit() and factiontid.isdigit():
        guildid = int(guildid)
        factiontid = int(factiontid)

        if kwargs["user"].factionid != factiontid or not kwargs["user"].factionaa:
            guild: ServerModel = ServerModel.objects(sid=guildid).first()

            if guild is None:
                return make_exception_response("1001", key)
            elif kwargs["user"].tid not in guild.admins:
                return make_exception_response("4020", key)
            elif factiontid not in guild.factions:
                return make_exception_response("1102", key)

            faction: FactionModel = FactionModel.objects(tid=factiontid).first()

            if faction is None:
                return make_exception_response("1102", key)
            elif faction.guild != guildid:
                return make_exception_response("1102", key)
        else:
            faction: FactionModel = FactionModel.objects(tid=kwargs["user"].factionid).first()
    else:
        if kwargs["user"].factionid == 0:
            return make_exception_response("1102", key)
        elif not kwargs["user"].factionaa:
            return make_exception_response("4005", key)

        faction: FactionModel = FactionModel.objects(tid=kwargs["user"].factionid).first()

    if faction is None:
        return make_exception_response("1102", key)
    elif utils.now() - faction.last_members >= 86400:  # one day
        return make_exception_response(
            "0000",
            key,
            details={"message": "The data hasn't been updated sufficiently recently."},
        )

    positions = PositionModel.objects(factiontid=faction.tid)

    if positions.count() == 0:
        return make_exception_response("1103", key)

    positions_data = []

    position: PositionModel
    for position in positions:
        position_data = json.loads(position.to_json())
        position_data["_id"] = str(position.pid)
        positions_data.append(position_data)

    return (jsonify({"positions": positions_data}), 200, api_ratelimit_response(key))
