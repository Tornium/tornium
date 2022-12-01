# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json

from controllers.api.decorators import *
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.factionmodel import FactionModel


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "faction:bot"})
def chain_config(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not kwargs["user"].factionaa:
        return make_exception_response("4005", key)
    elif kwargs["user"].factionid in ("", None, 0):
        return make_exception_response("1102", key)

    faction: FactionModel = FactionModel.objects(tid=kwargs["user"].factionid).first()

    if faction is None:
        return make_exception_response("1102", key)

    return (
        jsonify({"od": {"channel": faction.chainod["odchannel"]}}),
        200,
        api_ratelimit_response(key),
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "faction:bot"})
def chain_od_channel(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not kwargs["user"].factionaa:
        return make_exception_response("4005", key)

    channelid = data.get("channel")

    if channelid in ("", None, 0) or not channelid.isdigit():
        return make_exception_response("1002", key)
    elif kwargs["user"].factionid in ("", None, 0):
        return make_exception_response("1102", key)

    faction: FactionModel = FactionModel.objects(tid=kwargs["user"].factionid).first()

    if faction is None:
        return make_exception_response("1102", key)

    faction.chainconfig["odchannel"] = int(channelid)
    faction.save()

    return (
        jsonify({"od_channel": faction.chainod["odchannel"]}),
        200,
        api_ratelimit_response(key),
    )
