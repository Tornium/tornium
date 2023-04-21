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

from controllers.api.bot.config import jsonified_server_config
from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def banking_setter(guildid: int, factiontid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    channel_id = data.get("channel")
    roles_id = data.get("roles")

    if channel_id is None and roles_id is None:
        return make_exception_response("1000", key)
    elif channel_id is not None and (channel_id in ("", 0) or not channel_id.isdigit()):
        return make_exception_response("1002", key)
    elif roles_id is not None and type(roles_id) != list:
        return make_exception_response("1003", key)

    guild: ServerModel = ServerModel.objects(sid=guildid).first()
    faction: FactionModel = FactionModel.objects(tid=factiontid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif faction is None:
        return make_exception_response("1102", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif factiontid not in guild.factions or guild.sid != faction.guild:
        return make_exception_response("4021", key)

    banking_config = guild.banking_config.get(
        str(faction.tid),
        {
            "channel": "0",
            "roles": [],
        },
    )

    if channel_id is not None:
        banking_config["channel"] = channel_id

    if roles_id is not None:
        try:
            banking_config["roles"] = list(set(map(str, roles_id)))
        except TypeError:
            return make_exception_response("1003", key)

    guild.banking_config[str(faction.tid)] = banking_config
    guild.save()

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def banking_getter(guildid: int, factiontid: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    guild: ServerModel = ServerModel.objects(sid=guildid).first()
    faction: FactionModel = FactionModel.objects(tid=factiontid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif faction is None:
        return make_exception_response("1102", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif factiontid not in guild.factions or guild.sid != faction.guild:
        return make_exception_response("4021", key)

    banking_config = guild.banking_config.get(
        str(faction.tid),
        {
            "channel": "0",
            "roles": [],
        },
    )

    return (
        jsonify(
            {
                "channel": banking_config["channel"],
                "roles": banking_config["roles"],
            }
        ),
        200,
        api_ratelimit_response(key),
    )
