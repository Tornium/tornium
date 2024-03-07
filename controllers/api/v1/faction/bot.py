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

from peewee import fn
from tornium_commons.models import Faction, Server, User

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth()
@ratelimit
def add_assist_server(guild_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    user: User = kwargs["user"]

    if user.faction_id is None:
        return make_exception_response("1102", key)
    elif not user.faction_aa:
        return make_exception_response("4005", key)

    if guild_id is None or not isinstance(guild_id, int):
        return make_exception_response("", key)
    elif guild_id in user.faction.assist_servers:
        return make_exception_response("0000", key, details={"message": "Faction already has this guild set."})

    if not Server.select(Server.name).where(Server.sid == guild_id).exists():
        return make_exception_response("1001", key)

    Faction.update(assist_servers=fn.array_append(guild_id)).where(Faction.tid == user.faction.tid).execute()
    user.faction.assist_servers.append(guild_id)

    return (
        {
            "servers": [Server.server_str(sid) for sid in user.faction.assist_servers],
        },
        200,
        api_ratelimit_response(key),
    )


@require_oauth()
@ratelimit
def remove_assist_server(guild_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    user: User = kwargs["user"]

    if user.faction_id is None:
        return make_exception_response("1102", key)
    elif not user.faction_aa:
        return make_exception_response("4005", key)

    if guild_id is None or not isinstance(guild_id, int):
        return make_exception_response("", key)
    elif guild_id not in user.faction.assist_servers:
        return make_exception_response("0000", key, details={"message": "Faction does not have this guild set."})

    if not Server.select(Server.name).where(Server.sid == guild_id).exists():
        return make_exception_response("1001", key)

    Faction.update(assist_servers=fn.array_append(guild_id)).where(Faction.tid == user.faction.tid).execute()
    user.faction.assist_servers.remove(guild_id)

    return (
        {
            "servers": [Server.server_str(sid) for sid in user.faction.assist_servers],
        },
        200,
        api_ratelimit_response(key),
    )
