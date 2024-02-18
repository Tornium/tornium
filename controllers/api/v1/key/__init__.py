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
from peewee import IntegrityError
from tornium_commons.models import TornKey

from controllers.api.v1.decorators import (
    authentication_required,
    ratelimit,
    token_required,
)
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@authentication_required
@ratelimit
def test_key(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    return make_exception_response("0001", key)


@token_required
@ratelimit
def test_token(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    return make_exception_response("0001", key)


@token_required
@ratelimit
def set_key(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    api_key = data.get("key")

    if api_key in (None, "") or len(api_key) != 16:
        return make_exception_response("1200", key)

    try:
        TornKey.insert(api_key=api_key, user=None, default=False, disabled=False, paused=False, access_level=None)
    except IntegrityError:
        return make_exception_response("0000", key, details={"message": "Key already exists"})

    return (
        {
            "obfuscated_key": api_key[:6] + "*" * 10,
        },
        200,
        api_ratelimit_response(key),
    )
