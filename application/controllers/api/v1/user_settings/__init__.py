# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json

from flask import jsonify, request
from tornium_commons.models import UserSettings

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def toggle_cpr(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return make_exception_response("0000", key)

    settings = UserSettings.create_or_update(kwargs["user"].tid, cpr_enabled=enabled)

    return jsonify(settings.to_dict()), api_ratelimit_response(key)


@session_required
@ratelimit
def toggle_stat_db(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return make_exception_response("0000", key)

    settings = UserSettings.create_or_update(kwargs["user"].tid, stat_db_enabled=enabled)

    return jsonify(settings.to_dict()), api_ratelimit_response(key)


@session_required
@ratelimit
def toggle_od_drug(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return make_exception_response("0000", key)

    settings = UserSettings.create_or_update(kwargs["user"].tid, od_drug_enabled=enabled)

    return jsonify(settings.to_dict()), api_ratelimit_response(key)
