# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import jsonify, redirect, request
from flask_login import login_required

from models.servermodel import ServerModel


@login_required
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
