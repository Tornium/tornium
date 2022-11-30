# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json

from controllers.api.decorators import *
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.factionmodel import FactionModel
from models.positionmodel import PositionModel
from models.servermodel import ServerModel


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:faction", "faction:admin"})
def get_positions(*args, **kwargs):
    client = redisdb.get_redis()
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = request.args.get("guildid")
    factiontid = request.args.get("factiontid")

    if (
        guildid not in (None, 0, "")
        and factiontid not in (None, 0, "")
        and guildid.isdigit()
        and factiontid.isdigit()
    ):
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
            faction: FactionModel = FactionModel.objects(
                tid=kwargs["user"].factionid
            ).first()
    else:
        if kwargs["user"].factionid == 0:
            return make_exception_response("1102", key)
        elif not kwargs["user"].factionaa:
            return make_exception_response("4005", key)

        faction: FactionModel = FactionModel.objects(
            tid=kwargs["user"].factionid
        ).first()

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
