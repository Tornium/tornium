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

from tornium_commons.models import ServerModel

from controllers.api.bot.config import jsonified_server_config
from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def oc_config_setter(guildid, factiontid, notif, element, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if notif not in ("ready", "delay"):
        return make_exception_response("1000", key, details={"message": "Invalid notification type."})
    elif element not in ("roles", "channel"):
        return make_exception_response("1000", key, details={"message": "Invalid notification element."})

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

    if str(factiontid) not in oc_config:
        oc_config[str(factiontid)] = {
            "ready": {
                "channel": 0,
                "roles": [],
            },
            "delay": {
                "channel": 0,
                "roles": [],
            },
        }

    oc_config[str(factiontid)][notif][element] = elementid
    guild.oc_config = oc_config
    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
