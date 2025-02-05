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
import uuid

from peewee import DoesNotExist
from tornium_commons.models import GatewayClient, GatewayMessage

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


def _client_to_dict(client: GatewayClient) -> dict:
    return {
        "client_id": client.client_id,
        "user": client.user_id,
        "time_created": client.time_created.timestamp(),
        "revoked_in": client.revoked_in,
        "message": {
            "pending": GatewayMessage.select().where(GatewayMessage.recipient == client.user_id).count(),
        },
    }


@require_oauth("gateway")
@ratelimit
def create_gateway_client(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    client: GatewayClient = GatewayClient.create(
        client_id=uuid.uuid4().hex,
        user=kwargs["user"].tid,
        time_created=datetime.datetime.utcnow(),
        revoked_in=86400,
    )

    return _client_to_dict(client), 200, api_ratelimit_response(key)


@require_oauth("gateway")
@ratelimit
def get_gateway_client(client_id: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        client = (
            GatewayClient.select()
            .where((GatewayClient.client_id == client_id) & (GatewayClient.user == kwargs["user"].tid))
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1300", key)

    return _client_to_dict(client), 200, api_ratelimit_response(key)
