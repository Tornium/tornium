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

from flask import jsonify, redirect, request
from flask_login import fresh_login_required

from tornium_commons.models import ServerModel


@fresh_login_required
def assists_update(guildid):
    action = request.args.get("action")
    value = request.args.get("value")

    if action not in ["enable", "disable", "faction", "mod"]:
        return (
            jsonify({"success": False}),
            400,
            jsonify({"ContentType": "application/json"}),
        )

    server: ServerModel = ServerModel.objects(sid=guildid).first()

    if action == "faction":
        if int(value) in server.assist_factions:
            factions = server.assist_factions
            factions.remove(int(value))
            factions = list(set(factions))
            server.assist_factions = factions
            server.save()
        else:
            factions = server.assist_factions
            factions.append(int(value))
            factions = list(set(factions))
            server.assist_factions = factions
            server.save()
    elif action == "mod":
        if value.isdigit() and int(value) in (0, 1, 2):
            server.assist_mod = int(value)
            server.save()
        else:
            return (
                jsonify({"success": False}),
                400,
                jsonify({"ContentType": "application/json"}),
            )

    if request.method == "GET":
        return redirect(f"/bot/dashboard/{guildid}")
    else:
        return {"success": True}, 200, {"ContentType": "application/json"}
