# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json

from flask import render_template, abort, request, flash, redirect
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

    return render_template("bot/dashboard.html", servers=servers)


@login_required
def guild_dashboard(guildid: str):
    if guildid not in current_user.servers and not current_user.admin:
        abort(403)

    server = Server(guildid)
    factions = []
    assist_factions = []

    if request.method == "POST":
        if request.form.get("factionid") is not None:
            server_model = utils.first(ServerModel.objects(sid=guildid))
            server_model.factions.append(int(request.form.get("factionid")))
            server_model.factions = list(set(server_model.factions))
            server_model.save()
        elif (
            request.form.get("prefix") is not None
        ):  # TODO: Check if prefix is valid character
            if len(request.form.get("prefix")) != 1:
                flash("The length of the bot prefix must be one character long.")
                return render_template(
                    "bot/guild.html", server=server, factions=factions
                )

            server.prefix = request.form.get("prefix")
            server_model = utils.first(ServerModel.objects(sid=guildid))
            server_model.prefix = request.form.get("prefix")
            server_model.save()

    for faction in server.factions:
        factions.append(Faction(faction))

    for faction in server.assist_factions:
        assist_factions.append(Faction(faction))

    return render_template(
        "bot/guild.html",
        server=server,
        factions=factions,
        guildid=guildid,
        assist_factions=assist_factions,
        assist_mod=server.assist_mod,
    )


@login_required
def update_guild(guildid: str, factiontid: int):
    if guildid not in current_user.servers and not current_user.admin:
        abort(403)

    server_model = utils.first(ServerModel.objects(sid=guildid))
    server_model.factions.remove(factiontid)
    server_model.save()

    return redirect(f"/bot/dashboard/{guildid}")
