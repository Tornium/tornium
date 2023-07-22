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

import typing

from flask import abort, redirect, render_template, request
from flask_login import current_user, fresh_login_required, login_required
from tornium_commons.models import ServerModel

from models.faction import Faction


@login_required
def dashboard():
    servers = []

    for server in ServerModel.objects(admins=current_user.tid):
        if current_user.tid not in server.admins:
            continue

        servers.append(server)

    return render_template("bot/dashboard.html", servers=list(set(servers)))


@fresh_login_required
def guild_dashboard(guildid: str):
    server: typing.Optional[ServerModel] = ServerModel.objects(sid=guildid).first()

    if server is None:
        abort(400)
    elif current_user.tid not in server.admins:
        abort(403)

    factions = []
    assist_factions = []

    if request.method == "POST":
        if request.form.get("factionid") is not None:
            server.factions.append(int(request.form.get("factionid")))
            server.factions = list(set(server.factions))
            server.save()

    server_factions = [int(faction) for faction in server.factions]

    for faction in server.factions:
        try:
            factions.append(Faction(faction))
        except ValueError:
            server_factions.remove(int(faction))

    if server.factions != server_factions:
        server.factions = server_factions
        server.save()

    server_assist_factions = [int(faction) for faction in server.assist_factions]

    for faction in server.assist_factions:
        try:
            assist_factions.append(Faction(faction))
        except ValueError:
            server_factions.remove(int(faction))

    if server.assist_factions != server_assist_factions:
        server.assist_factions = server_assist_factions
        server.save()

    return render_template(
        "bot/guild.html",
        server=server,
        factions=factions,
        guildid=guildid,
        assist_factions=assist_factions,
    )


@fresh_login_required
def update_guild(guildid: str, factiontid: int):
    server_model = ServerModel.objects(sid=guildid).first()

    if current_user.tid not in server_model.admins:
        abort(403)

    server_model.factions.remove(factiontid)
    server_model.save()

    return redirect(f"/bot/dashboard/{guildid}")
