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
import typing

from flask import request
from peewee import DoesNotExist
from tornium_commons.models import Notification, Server, ServerNotificationsConfig

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def get_notification_config(guild_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild: Server = (
            Server.select(Server.admins, Server.notifications_config)
            .join(ServerNotificationsConfig)
            .where(Server.sid == guild_id)
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    return (
        {
            "enabled": guild.notifications_config.enabled,
            "log_channel": str(guild.notifications_config.log_channel),
        },
        200,
        api_ratelimit_response(key),
    )


@session_required
@ratelimit
def toggle_notifications(guild_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    data = json.loads(request.get_data().decode("utf-8"))

    enabled: typing.Optional[bool] = data.get("enabled")

    if enabled is None or not isinstance(enabled, bool):
        return make_exception_response("1000", key, details={"message": "Invalid enabled value"})

    try:
        guild: Server = (
            Server.select(Server.admins, Server.notifications_config)
            .where(Server.sid == guild_id)
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    ServerNotificationsConfig.update(enabled=enabled).where(
        ServerNotificationsConfig.id == guild.notifications_config_id
    ).execute()

    return {}, 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_notifications_log_channel(guild_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    data = json.loads(request.get_data().decode("utf-8"))

    try:
        channel_id = int(data["channel_id"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = (
            Server.select(Server.admins, Server.notifications_config)
            .where(Server.sid == guild_id)
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    ServerNotificationsConfig.update(log_channel=channel_id).where(
        ServerNotificationsConfig.id == guild.notifications_config_id
    ).execute()

    return {}, 200, api_ratelimit_response(key)


@session_required
@ratelimit
def get_server_notifications(guild_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    limit = request.args.get("limit", 10)
    offset = request.args.get("offset", 0)

    if (not isinstance(limit, str) or not limit.isdigit()) and not isinstance(limit, int):
        return make_exception_response("1000", key, details={"error": "Invalid limit value"})
    elif int(limit) <= 0:
        return make_exception_response("1000", key, details={"error": "Invalid limit value"})
    elif (not isinstance(offset, str or not limit.isdigit())) and not isinstance(offset, int):
        return make_exception_response("1000", key, details={"error": "Invalid offset value"})
    elif int(offset) < 0:
        return make_exception_response("1000", key, details={"error": "Invalid offset value"})

    limit = int(limit)
    offset = int(offset)

    server_notifications = Notification.select().where(Notification.server_id == guild_id)
    filtered_server_notifications = server_notifications.offset(offset).limit(limit)

    return (
        {
            "count": server_notifications.count(),
            "notifications": [notification.as_dict() for notification in filtered_server_notifications],
        },
        200,
        api_ratelimit_response(key),
    )
