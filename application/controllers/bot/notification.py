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

import uuid

from flask import render_template
from flask_login import current_user, fresh_login_required
from peewee import DoesNotExist
from tornium_commons.models import Server, ServerNotificationsConfig, Notification


@fresh_login_required
def notification_dashboard(guild_id: int):
    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Guild Not Found",
                error="No Discord server could be located with the passed guild ID",
            ),
            400,
        )

    if current_user.tid not in guild.admins:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error="Only server admins are able to access this page, and you do not have this permission.",
            ),
            403,
        )

    if guild.notifications_config is None:
        notifications_config: ServerNotificationsConfig = ServerNotificationsConfig.create()
        guild = (
            Server.update(notifications_config=notifications_config._pk)
            .where(Server.sid == guild_id)
            .returning(Server)
            .execute()[0]
        )

    return render_template("bot/notification.html", guild=guild)


@fresh_login_required
def view_notification(guild_id: int, notification_uuid: str):
    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Guild Not Found",
                error="No Discord server could be located with the passed guild ID",
            ),
            400,
        )

    if current_user.tid not in guild.admins:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error="Only server admins are able to access this page, and you do not have this permission.",
            ),
            403,
        )

    try:
        notification: Notification = (
            Notification.select().where(Notification.nid == uuid.UUID(notification_uuid)).get()
        )
    except ValueError:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Notification UUID",
                error=f'The provided notification UUID "{notification_uuid}" is not formatted correctly.',
            ),
            400,
        )
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Notification ID",
                error=f'There does not exist a notification of ID "{notification_uuid}".',
            ),
            400,
        )

    return render_template("notification/trigger_server_setup.html", trigger=notification.trigger, guild=guild, update=True, notification=notification)
