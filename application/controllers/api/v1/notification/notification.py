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
import uuid

from flask import request
from peewee import DoesNotExist
from tornium_commons.models import Notification

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def update_guild_notification(notification_id, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        notification_uuid = uuid.UUID(notification_id)
    except ValueError:
        return make_exception_response("1000", key, details={"message": "Invalid notification UUID"})

    try:
        notification: Notification = (
            Notification.select().where(Notification.nid == notification_uuid).get()
        )  # TODO: Limit selections
    except DoesNotExist:
        return make_exception_response("1401", key)

    if kwargs["user"].tid not in notification.server.admins:
        return make_exception_response("4020", key)

    try:
        channel_id = int(data["channel_id"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        resource_id = int(data["resource_id"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1000", key, details={"message": "Invalid resource ID"})

    if resource_id == 0:
        return make_exception_response("1000", key, details={"message": "Invalid resource ID: must not be zero"})

    try:
        one_shot = data["one_shot"]
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1000", key, details={"message": "Invalid one-shot value"})

    if not isinstance(one_shot, bool):
        return make_exception_response("1000", key, details={"message": "Invalid one-shot value"})

    try:
        parameters = data["parameters"]
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1402", key)

    if not isinstance(parameters, dict):
        return make_exception_response("1402", key)
    elif not all(isinstance(key, str) for key in parameters.keys()):
        return make_exception_response("1402", key)
    elif parameters.keys() != notification.trigger.parameters.keys():
        return make_exception_response("1402", key, details={"message": "Invalid parameter key"})

    Notification.update(channel_id=channel_id, resource_id=resource_id, one_shot=one_shot, parameters=parameters).where(
        Notification.nid == notification_uuid
    ).execute()

    return (
        {
            "nid": notification.nid,
        },
        200,
        api_ratelimit_response(key),
    )


@session_required
@ratelimit
def delete_guild_notification(notification_id, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        notification_uuid = uuid.UUID(notification_id)
    except ValueError:
        return make_exception_response("1000", key, details={"message": "Invalid notification UUID"})

    try:
        notification: Notification = (
            Notification.select().where(Notification.nid == notification_uuid).get()
        )  # TODO: Limit selections
    except DoesNotExist:
        return make_exception_response("1401", key)

    if kwargs["user"].tid not in notification.server.admins:
        return make_exception_response("4020", key)

    notification.delete_instance()

    return {}, 200, api_ratelimit_response(key)
