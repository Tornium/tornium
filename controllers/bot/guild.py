# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

import json

from flask import render_template, abort, request, flash,redirect
from flask_login import login_required, current_user

from models.faction import Faction
from models.server import Server
from models.servermodel import ServerModel
import utils


@login_required
def dashboard():
    servers = []

    for server in current_user.servers:
        servers.append(Server(int(server)))

    return render_template('bot/dashboard.html', servers=servers)


@login_required
def guild_dashboard(guildid: str):
    if guildid not in current_user.servers:
        abort(403)

    server = Server(guildid)
    factions = []

    if request.method == 'POST':
        if request.form.get('factionid') is not None:
            server_model = utils.first(ServerModel.objects(sid=guildid))
            server_model.factions.append(int(request.form.get('factionid')))
            server_model.factions = list(set(server_model.factions))
            server_model.save()
        elif request.form.get('prefix') is not None:  # TODO: Check if prefix is valid character
            if len(request.form.get('prefix')) != 1:
                flash('The length of the bot prefix must be one character long.')
                return render_template('bot/guild.html', server=server, factions=factions)

            server.prefix = request.form.get('prefix')
            server_model = utils.first(ServerModel.objects(sid=guildid))
            server_model.prefix = request.form.get('prefix')
            server_model.save()

    for faction in server.factions:
        factions.append(Faction(faction))

    return render_template('bot/guild.html', server=server, factions=factions, guildid=guildid)


@login_required
def update_guild(guildid: str, factiontid: int):
    if guildid not in current_user.servers:
        abort(403)

    server_model = utils.first(ServerModel.objects(sid=guildid))
    server_model.factions.remove(factiontid)
    server_model.save()

    return redirect(f'/bot/dashboard/{guildid}')
