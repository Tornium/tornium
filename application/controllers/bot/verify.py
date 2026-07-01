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

from flask import render_template
from flask_login import current_user, login_required
from peewee import DoesNotExist, fn
from tornium_commons.formatters import rel_time
from tornium_commons.models import Server, VerificationLog


@login_required
def verify_dashboard(guild_id: int):
    try:
        guild: Server = (
            Server.select(
                Server.sid,
                Server.verify_enabled,
                Server.verify_template,
                Server.auto_verify_enabled,
                Server.gateway_verify_enabled,
                Server.faction_verify,
                Server.admins,
            )
            .where(Server.sid == guild_id)
            .get()
        )
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

    one_day_ago = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    verification_stats = (
        VerificationLog.select(
            fn.COUNT(VerificationLog.guid).alias("verification_attempts"),
            fn.COUNT(VerificationLog.guid).filter(VerificationLog.error_type.is_null(False)).alias("failed_attempts"),
            fn.MAX(VerificationLog.timestamp).alias("most_recent_timestamp"),
        )
        .where((VerificationLog.server_id == guild_id) & (VerificationLog.timestamp >= one_day_ago))
        .dicts()
        .get()
    )

    verification_stats_dict = {
        "verification_attempts": "N/A",
        "verification_failed_attempts": "N/A",
        "verification_most_recent_timestamp": "N/A",
        "verification_success_percent": "N/A",
    }

    if verification_stats["verification_attempts"] > 0:
        verification_stats_dict["verification_attempts"] = verification_stats["verification_attempts"]
        verification_stats_dict["verification_failed_attempts"] = verification_stats["failed_attempts"]
        verification_stats_dict["verification_most_recent_timestamp"] = rel_time(
            verification_stats["most_recent_timestamp"]
        )
        verification_stats_dict["verification_success_percent"] = round(
            (verification_stats["verification_attempts"] - verification_stats["failed_attempts"])
            / verification_stats["verification_attempts"]
            * 100
        )

    return render_template("bot/verify.html", guild=guild, **verification_stats_dict)


@login_required
def verify_logs(guild_id: int):
    try:
        guild: Server = Server.select(Server.sid, Server.admins).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Guild Not Found",
                error="No Discord server could be located with the provided guild ID",
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

    return render_template("bot/verify-logs.html", guild=guild)
