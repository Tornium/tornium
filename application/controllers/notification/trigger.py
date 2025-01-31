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

import random
import uuid

from flask import render_template
from flask_login import current_user, fresh_login_required, login_required
from peewee import DoesNotExist
from tornium_commons.models import Notification, NotificationTrigger, Server


@login_required
def triggers():
    return render_template("notification/trigger.html")


@login_required
def trigger_create():
    return render_template(
        "notification/trigger_create.html",
        create=True,
        trigger_name=f"trigger-{current_user.tid}-{random.randint(0, 100)}",
        trigger_description="",
        trigger_cron="* * * * *",
        trigger_code="",
        trigger_parameters={},
        trigger_message_type=0,
        trigger_message_template="",
    )


@login_required
def trigger_get(trigger_uuid: str):
    try:
        trigger: NotificationTrigger = (
            NotificationTrigger.select().where(NotificationTrigger.tid == uuid.UUID(trigger_uuid)).get()
        )
    except ValueError:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Trigger UUID",
                error=f'The provided trigger UUID "{trigger_uuid}" is not formatted correctly.',
            ),
            400,
        )
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Trigger ID",
                error=f'There does not exist a trigger of ID "{trigger_uuid}".',
            ),
            400,
        )

    return render_template(
        "notification/trigger_create.html",
        create=False,
        trigger_uuid=trigger_uuid,
        trigger_name=trigger.name,
        trigger_description=trigger.description,
        trigger_resource=trigger.resource,
        trigger_cron=trigger.cron,
        trigger_code=trigger.code,
        trigger_parameters=trigger.parameters,  # TODO: Add option to use pre-determine values in dynamic list component
        trigger_message_type=trigger.message_type,
        trigger_message_template=trigger.message_template,
    )


@fresh_login_required
def trigger_add_server(trigger_uuid: str):
    try:
        trigger: NotificationTrigger = (
            NotificationTrigger.select().where(NotificationTrigger.tid == uuid.UUID(trigger_uuid)).get()
        )
    except ValueError:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Trigger UUID",
                error=f'The provided trigger UUID "{trigger_uuid}" is not formatted correctly.',
            ),
            400,
        )
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Trigger ID",
                error=f'There does not exist a trigger of ID "{trigger_uuid}".',
            ),
            400,
        )

    return render_template("notification/trigger_server_add.html", trigger=trigger)


@fresh_login_required
def trigger_setup_server(trigger_uuid: str, guild_id: int):
    try:
        trigger: NotificationTrigger = (
            NotificationTrigger.select().where(NotificationTrigger.tid == uuid.UUID(trigger_uuid)).get()
        )
    except ValueError:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Trigger UUID",
                error=f'The provided trigger UUID "{trigger_uuid}" is not formatted correctly.',
            ),
            400,
        )
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Trigger ID",
                error=f'There does not exist a trigger of ID "{trigger_uuid}".',
            ),
            400,
        )

    try:
        guild: Server = Server.select(Server.name, Server.sid, Server.admins).where(Server.sid == int(guild_id)).get()
    except (ValueError, TypeError, DoesNotExist):
        return (
            render_template(
                "errors/error.html",
                title="Server Not Found",
                error="The server ID could not be located in the database.",
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

    return render_template(
        "notification/trigger_server_setup.html", trigger=trigger, guild=guild, notification=None, update=False
    )
