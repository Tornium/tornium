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
from tornium_commons.models import Server, ServerNotificationsConfig

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def get_notification_config(guild_id, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild: Server = Server.get_by_id(guild_id)  # TODO: Limit selections
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    return (
        {
            "enabled": guild.notifications_config.enabled,
            "log_channel": guild.notifications_config.log_channel,
        },
        200,
        api_ratelimit_response(key),
    )


@session_required
@ratelimit
def toggle_notifications(guild_id, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    data = json.loads(request.get_data().decode("utf-8"))

    enabled: typing.Optional[bool] = data.get("enabled")

    if enabled is None or not isinstance(enabled, bool):
        return make_exception_response("1000", key, details={"message": "Invalid enabled value"})

    try:
        guild: Server = Server.get_by_id(guild_id)  # TODO: Limit selections
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
def set_notifications_log_channel(guild_id, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    data = json.loads(request.get_data().decode("utf-8"))

    try:
        channel_id = int(data["channel_id"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = Server.get_by_id(guild_id)  # TODO: Limit selections
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    ServerNotificationsConfig.update(log_channel=channel_id).where(
        ServerNotificationsConfig.id == guild.notifications_config_id
    ).execute()

    return {}, 200, api_ratelimit_response(key)
