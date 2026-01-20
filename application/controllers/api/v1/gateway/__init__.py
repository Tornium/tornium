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

import datetime
import json
import secrets
import os
import uuid

from flask import request
from peewee import DoesNotExist
from tornium_commons.models import GatewayToken

from controllers.api.v1.decorators import ratelimit, session_required, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response
from controllers.authroutes import _log_auth

GATEWAY_HOST = os.environ.get("GATEWAY_HOST") or "https://gateway.tornium.com/"

# NOTE: secrets.token_hex generates double the number of characters as the number of bytes inputted
TOKEN_LENGTH = 64


@require_oauth("gateway")
@ratelimit
def create_token(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    token = GatewayToken.create(
        guid=uuid.uuid4(),
        user_id=kwargs["user"].tid,
        token=secrets.token_hex(TOKEN_LENGTH / 2),
        created_at=datetime.datetime.utcnow(),
        created_ip=request.headers.get("CF-Connecting-IP") or request.remote_addr,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
    )

    return (
        {"token": token.token, "expires_at": token.expires_at.timestamp(), "gateway_url": f"{GATEWAY_HOST}/"},
        200,
        api_ratelimit_response(key),
    )


@require_oauth("gateway")
@ratelimit
def revoke_token(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    token = data.get("token")

    if token is None or not isinstance(token, str) or len(token) != TOKEN_LENGTH:
        return make_exception_response("1300", key)

    try:
        gateway_token: GatewayToken = (
            GatewayToken.select()
            .where((GatewayToken.token == token) & (GatewayToken.user_id == kwargs["user"].tid))
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1300", key)

    gateway_token.delete_instance()

    return "", 204, api_ratelimit_response(key)
