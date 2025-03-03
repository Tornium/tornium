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

import typing

from flask import jsonify
from tornium_commons.models import OrganizedCrimeNew

from controllers.api.v1.decorators import global_cache, ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response


@require_oauth()
@ratelimit
@global_cache
def get_oc_names(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    oc_names: typing.List[str] = [
        crime.oc_name for crime in OrganizedCrimeNew.select().distinct(OrganizedCrimeNew.oc_name)
    ]

    return jsonify(oc_names), 200, api_ratelimit_response(key)
