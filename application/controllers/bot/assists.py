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

from flask import jsonify, redirect, render_template, request
from flask_login import current_user, fresh_login_required
from peewee import DoesNotExist
from tornium_commons.models import Server


# TODO: Make this be more logical (and an API endpoint)
@fresh_login_required
def assists_update(guild_id):
    action = request.args.get("action")
    value = request.args.get("value")

    if action != "faction":
        return (
            jsonify({"success": False}),
            400,
            jsonify({"ContentType": "application/json"}),
        )

    try:
        guild: Server = Server.get_by_id(guild_id)
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

    if action == "faction":
        if int(value) in guild.assist_factions:
            factions = guild.assist_factions
            factions.remove(int(value))
            factions = list(set(factions))
            guild.assist_factions = factions
            guild.save()
        else:
            factions = guild.assist_factions
            factions.append(int(value))
            factions = list(set(factions))
            guild.assist_factions = factions
            guild.save()

    if request.method == "GET":
        return redirect(f"/bot/dashboard/{guild_id}")
    else:
        return {"success": True}, 200, {"ContentType": "application/json"}
