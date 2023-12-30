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
from tornium_commons.models import Faction

from controllers.api.v1.decorators import ratelimit, token_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@token_required
@ratelimit
def chain_config(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not kwargs["user"].faction_aa:
        return make_exception_response("4005", key)
    elif kwargs["user"].faction is None:
        return make_exception_response("1102", key)

    return (
        jsonify({"od": {"channel": kwargs["user"].faction.od_channel}}),
        200,
        api_ratelimit_response(key),
    )


@token_required
@ratelimit
def chain_od_channel(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not kwargs["user"].faction_aa:
        return make_exception_response("4005", key)
    elif kwargs["user"].faction is None:
        return make_exception_response("1102", key)

    try:
        channel_id = int(data["channel"])
    except (KeyError, TypeError, ValueError):
        return make_exception_response("1002", key)

    Faction.update(od_channel=int(channel_id)).where(Faction.tid == kwargs["user"].faction_id).execute()

    return (
        jsonify({"od_channel": int(channel_id)}),
        200,
        api_ratelimit_response(key),
    )
