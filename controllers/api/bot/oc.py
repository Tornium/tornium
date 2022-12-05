# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json

from controllers.api.bot.config import jsonified_server_config
from controllers.api.decorators import *
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.servermodel import ServerModel


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def oc_config_setter(guildid, factiontid, notif, element, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if notif not in ("ready", "delay"):
        return make_exception_response(
            "1000", key, details={"message": "Invalid notification type."}
        )
    elif element not in ("roles", "channel"):
        return make_exception_response(
            "1000", key, details={"message": "Invalid notification element."}
        )

    if guildid in ("", None, 0) or not guildid.isdigit():
        return make_exception_response("1001", key)

    data = json.loads(request.get_data().decode("utf-8"))
    elementid = data.get(element)

    if elementid in ("", None, 0):
        return make_exception_response("1000", key)
    elif element not in ("roles") and not elementid.isdigit():
        return make_exception_response("1000", key)

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif factiontid not in guild.factions:
        return make_exception_response("4021", key)

    oc_config = guild.oc_config

    if factiontid not in oc_config:
        oc_config[factiontid] = {
            "ready": {
                "channel": 0,
                "roles": [],
            },
            "delay": {
                "channel": 0,
                "roles": [],
            },
        }

    oc_config[factiontid][notif][element] = elementid
    guild.oc_config = oc_config
    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
