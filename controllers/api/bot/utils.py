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

from controllers.api.decorators import ratelimit, token_required
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.server import Server


@token_required
@ratelimit
def get_channels(guildid, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        server = Server(guildid)
    except LookupError:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in server.admins:
        return make_exception_response("4020", key)

    return (
        {"channels": server.get_text_channels(api=True)},
        200,
        api_ratelimit_response(key),
    )


@token_required
@ratelimit
def get_roles(guildid, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        server = Server(guildid)
    except LookupError:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in server.admins:
        return make_exception_response("4020", key)

    return (
        {"roles": list(server.get_roles(api=True).values())},
        200,
        api_ratelimit_response(key),
    )
