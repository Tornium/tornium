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

from tornium_commons.models import FactionModel

from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response


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
        jsonify({"od": {"channel": faction.chainconfig["odchannel"]}}),
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
        jsonify({"od_channel": faction.chainconfig["odchannel"]}),
        200,
        api_ratelimit_response(key),
    )
