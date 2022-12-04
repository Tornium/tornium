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
def assists_channel(guildid, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    channelid = data.get("channel")

    if guildid in ("", None, 0) or not guildid.isdigit():
        return make_exception_response("1001", key)
    elif channelid in ("", None, 0) or not channelid.isdigit():
        return make_exception_response("1002", key)

    channelid = int(channelid)
    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    guild.assistschannel = channelid
    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
