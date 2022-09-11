# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import json

import honeybadger
from flask import request, jsonify, render_template, redirect, flash
from flask_login import login_required, current_user

from models.faction import Faction
from models.factionstakeoutmodel import FactionStakeoutModel
from models.server import Server
from models.servermodel import ServerModel
from models.stakeout import Stakeout
from models.user import User
import tasks
import utils
from models.userstakeoutmodel import UserStakeoutModel


@login_required
def stakeouts_dashboard(guildid: str):
    server: ServerModel = ServerModel.objects(sid=guildid).first()

    if server is None:
        return (
            render_template(
                "errors/error.html", title="Error", error="Server not found."
            ),
            400,
        )
    elif current_user.tid not in server.admins:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error=f"{current_user.name} [{current_user.tid}] is required to be an administrator "
                f"of {server.name}.",
            ),
            403,
        )

    if request.method == "POST":
        if request.form.get("factionid") is not None:
            if int(request.form.get("factionid")) not in server.factionstakeouts:
                stakeout = Stakeout(
                    int(request.form.get("factionid")),
                    user=False,
                    key=current_user.key,
                    guild=int(guildid),
                )
                stakeouts = server.factionstakeouts
                stakeouts.append(int(request.form.get("factionid")))
                server.factionstakeouts = list(set(stakeouts))
                server.save()

                if server.stakeoutconfig["category"] != 0:
                    payload = {
                        "name": f'faction-{stakeout.data["name"]}',
                        "type": 0,
                        "topic": f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                        f'[{stakeout.data["ID"]}] by the Tornium bot.',
                        "parent_id": server.stakeoutconfig["category"],
                    }  # TODO: Add permission overwrite: everyone write false
                else:
                    payload = {
                        "name": f'faction-{stakeout.data["name"]}',
                        "type": 0,
                        "topic": f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                        f'[{stakeout.data["ID"]}] by the Tornium bot.',
                    }  # TODO: Add permission overwrite: everyone write false

                channel = tasks.discordpost(
                    f"guilds/{guildid}/channels", payload=payload, dev=server.skynet
                )

                db_stakeout = FactionStakeoutModel.objects(
                    tid=request.form.get("factionid")
                ).first()
                db_stakeout.guilds[str(guildid)]["channel"] = int(channel["id"])
                db_stakeout.save()

                message_payload = {
                    "embeds": [
                        {
                            "title": "Faction Stakeout Creation",
                            "description": f'A stakeout of faction {stakeout.data["name"]} has been created in '
                            f"{server.name}. This stakeout can be setup or removed in the "
                            f"[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{server.sid}) by a "
                            f"server administrator.",
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                        }
                    ]
                }
                tasks.discordpost(
                    f'channels/{channel["id"]}/messages',
                    payload=message_payload,
                    dev=server.skynet,
                )
            else:
                flash(
                    f'Faction ID {request.form.get("factionid")} is already being staked out in {server.name}.',
                    category="error",
                )
        elif request.form.get("userid") is not None:
            if int(request.form.get("userid")) not in server.userstakeouts:
                stakeout = Stakeout(
                    int(request.form.get("userid")),
                    key=current_user.key,
                    guild=int(guildid),
                )
                server.userstakeouts.append(int(request.form.get("userid")))
                server.userstakeouts = list(set(server.userstakeouts))
                server.save()

                if server.stakeoutconfig["category"] != 0:
                    payload = {
                        "name": f'user-{stakeout.data["name"]}',
                        "type": 0,
                        "topic": f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                        f'[{stakeout.data["player_id"]}] by the Tornium bot.',
                        "parent_id": server.stakeoutconfig["category"],
                    }  # TODO: Add permission overwrite: everyone write false
                else:
                    payload = {
                        "name": f'user-{stakeout.data["name"]}',
                        "type": 0,
                        "topic": f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                        f'[{stakeout.data["player_id"]}] by the Tornium bot.',
                    }  # TODO: Add permission overwrite: everyone write false

                channel = tasks.discordpost(
                    f"guilds/{guildid}/channels", payload=payload, dev=server.skynet
                )

                db_stakeout = UserStakeoutModel.objects(
                    tid=request.form.get("userid")
                ).first()
                db_stakeout.guilds[str(guildid)]["channel"] = int(channel["id"])
                db_stakeout.save()

                message_payload = {
                    "embeds": [
                        {
                            "title": "User Stakeout Creation",
                            "description": f'A stakeout of user {stakeout.data["name"]} has been created in '
                            f"{server.name}. This stakeout can be setup or removed in the "
                            f"[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{server.sid}) by a "
                            f"server administrator.",
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                        }
                    ]
                }
                tasks.discordpost(
                    f'channels/{channel["id"]}/messages',
                    payload=message_payload,
                    dev=server.skynet,
                )
            else:
                flash(
                    f'User ID {request.form.get("userid")} is already being staked out in {server.name}.',
                    category="error",
                )

    return render_template("bot/stakeouts.html", guildid=guildid)


@login_required
def stakeouts(guildid: str, stype: int):
    server: ServerModel = ServerModel.objects(sid=guildid).first()

    if server is None:
        return (
            render_template(
                "errors/error.html", title="Error", error="Server not found."
            ),
            400,
        )
    elif current_user.tid not in server.admins:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error=f"{current_user.name} [{current_user.tid}] is required to be an administrator "
                f"of {server.name}.",
            ),
            403,
        )

    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    stakeouts = []

    if stype == 0:  # user
        filtered = len(server.userstakeouts)

        stakeout: int
        for stakeout in server.userstakeouts:
            stakeout: Stakeout = Stakeout(int(stakeout), key=current_user.key)

            if str(guildid) not in stakeout.guilds:
                honeybadger.honeybadger.notify(
                    error_class="Exception",
                    error_message=f"{guildid} not in the guilds of {stakeout.tid}",
                    context={"guildid": guildid, "tid": stakeout.tid},
                )

                user_stakeouts = server.userstakeouts
                user_stakeouts.remove(stakeout.tid)
                server.userstakeouts = user_stakeouts
                server.save()
                continue

            stakeouts.append(
                [
                    stakeout.tid,
                    stakeout.guilds[str(guildid)]["keys"],
                    utils.rel_time(
                        datetime.datetime.fromtimestamp(stakeout.last_update)
                    ),
                ]
            )
    elif stype == 1:  # faction
        filtered = len(server.factionstakeouts)
        for stakeout in server.factionstakeouts:
            stakeout: Stakeout = Stakeout(
                int(stakeout), user=False, key=current_user.key
            )

            if str(guildid) not in stakeout.guilds:
                honeybadger.honeybadger.notify(
                    error_class="Exception",
                    error_message=f"{guildid} not in the guilds of {stakeout.tid}",
                    context={"guildid": guildid, "tid": stakeout.tid},
                )
                faction_stakeouts = server.factionstakeouts
                faction_stakeouts.remove(stakeout.tid)
                server.factionstakeouts = faction_stakeouts
                server.save()
                continue

            stakeouts.append(
                [
                    stakeout.tid,
                    stakeout.guilds[str(guildid)]["keys"],
                    utils.rel_time(
                        datetime.datetime.fromtimestamp(stakeout.last_update)
                    ),
                ]
            )
    else:
        filtered = 0

    stakeouts = stakeouts[start : start + length]
    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": len(server.userstakeouts) + len(server.factionstakeouts),
        "recordsFiltered": filtered,
        "data": stakeouts,
    }
    return data


@login_required
def stakeout_data(guildid: str):
    server: ServerModel = ServerModel.objects(sid=guildid).first()

    if server is None:
        return (
            render_template(
                "errors/error.html", title="Error", error="Server not found."
            ),
            400,
        )
    elif current_user.tid not in server.admins:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error=f"{current_user.name} [{current_user.tid}] is required to be an administrator "
                f"of {server.name}.",
            ),
            403,
        )

    faction = request.args.get("faction")
    user = request.args.get("user")

    if (not faction and not user) or (faction and user):
        raise Exception  # TODO: make exception more descriptive

    if faction:
        if int(faction) not in server.factionstakeouts:
            raise Exception

        stakeout = Stakeout(faction, user=False)

        return render_template(
            "bot/factionstakeoutmodal.html",
            faction=f"{Faction(int(faction), key=current_user.key).name} [{faction}]",
            lastupdate=utils.rel_time(
                datetime.datetime.fromtimestamp(stakeout.last_update)
            ),
            keys=stakeout.guilds[str(guildid)]["keys"],
            guildid=guildid,
            tid=faction,
            armory=(
                int(faction) in Server(guildid).factions
                or Faction(faction).guild == int(guildid)
            ),
        )
    elif user:
        if int(user) not in server.userstakeouts:
            raise Exception

        stakeout = Stakeout(user)
        return render_template(
            "bot/userstakeoutmodal.html",
            user=f"{User(int(user), key=current_user.key).name} [{user}]",
            lastupdate=utils.rel_time(
                datetime.datetime.fromtimestamp(stakeout.last_update)
            ),
            keys=stakeout.guilds[str(guildid)]["keys"],
            guildid=guildid,
            tid=user,
        )


@login_required
def stakeout_update(guildid):
    server: ServerModel = ServerModel.objects(sid=guildid).first()

    if server is None:
        return (
            render_template(
                "errors/error.html", title="Error", error="Server not found."
            ),
            400,
        )
    elif current_user.tid not in server.admins:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error=f"{current_user.name} [{current_user.tid}] is required to be an administrator "
                f"of {server.name}.",
            ),
            403,
        )

    action = request.args.get("action")
    faction = request.args.get("faction")
    user = request.args.get("user")
    value = request.args.get("value")

    if action not in ["remove", "addkey", "removekey", "enable", "disable", "category"]:
        return json.dumps({"success": False}), 400, {"ContentType": "application/json"}
    elif faction and user:
        return json.dumps({"success": False}), 400, {"ContentType": "application/json"}

    if action == "remove":
        server = ServerModel.objects(sid=guildid).first()

        if faction is not None:
            server.factionstakeouts.remove(int(faction))

            stakeout = FactionStakeoutModel.objects(tid=faction).first()
            try:
                tasks.discorddelete(
                    f'channels/{stakeout.guilds[str(guildid)]["channel"]}',
                    dev=server.skynet,
                )
            except utils.DiscordError as e:
                if e.code == 10003:
                    pass
                else:
                    raise e
            stakeout.guilds.pop(str(guildid))

            if len(stakeout.guilds) == 0:
                stakeout.delete()
            else:
                stakeout.save()
        elif user is not None:
            server.userstakeouts.remove(int(user))

            stakeout = UserStakeoutModel.objects(tid=user).first()
            try:
                tasks.discorddelete(
                    f'channels/{stakeout.guilds[str(guildid)]["channel"]}',
                    dev=server.skynet,
                )
            except utils.DiscordError as e:
                if e.code == 10003:
                    pass
                else:
                    raise e
            stakeout.guilds.pop(str(guildid))

            if len(stakeout.guilds) == 0:
                stakeout.delete()
            else:
                stakeout.save()

        server.save()
    elif action == "addkey":
        if faction is not None and value not in [
            "territory",
            "members",
            "memberstatus",
            "memberactivity",
            "armory",
            "assault",
            "armorydeposit",
        ]:
            return (
                jsonify(
                    {
                        "error": f"Faction is set to {faction} for a key that doesn't allow a faction "
                        f"ID to be passed."
                    }
                ),
                400,
            )
        elif user is not None and value not in [
            "level",
            "status",
            "flyingstatus",
            "online",
            "offline",
        ]:
            return (
                jsonify(
                    {
                        "error": f"User is set to {user} for a key that doesn't allow a user "
                        f"ID to be passed."
                    }
                ),
                400,
            )
        elif value == "armory" and (
            int(faction) not in Server(guildid).factions
            or Faction(faction).guild != int(guildid)
        ):
            return (
                jsonify(
                    {
                        "error": f"This requires the faction to be in the list of factions in the server."
                    }
                ),
                400,
            )

        if user is not None:
            stakeout = UserStakeoutModel.objects(tid=user).first()
        else:
            stakeout = FactionStakeoutModel.objects(tid=faction).first()

        if value in stakeout.guilds[str(guildid)]["keys"]:
            return (
                jsonify(
                    {"error": f"Value {value} is already in {guildid}'s list of keys."}
                ),
                400,
            )

        stakeout.guilds[str(guildid)]["keys"].append(value)
        stakeout.save()
    elif action == "removekey":
        if faction is not None and value not in [
            "territory",
            "members",
            "memberstatus",
            "memberactivity",
            "armory",
            "assault",
            "armorydeposit",
        ]:
            return (
                jsonify(
                    {
                        "error": f"Faction is set to {faction} for a key that doesn't allow a faction "
                        f"ID to be passed."
                    }
                ),
                400,
            )
        elif user is not None and value not in [
            "level",
            "status",
            "flyingstatus",
            "online",
            "offline",
        ]:
            return (
                jsonify(
                    {
                        "error": f"User is set to {user} for a key that doesn't allow a user "
                        f"ID to be passed."
                    }
                ),
                400,
            )

        if user is not None:
            stakeout = UserStakeoutModel.objects(tid=user).first()
        else:
            stakeout = FactionStakeoutModel.objects(tid=faction).first()

        if value not in stakeout.guilds[str(guildid)]["keys"]:
            return (
                jsonify(
                    {"error": f"Value {value} is not in {guildid}'s list of keys."}
                ),
                400,
            )

        stakeout.guilds[str(guildid)]["keys"].remove(value)
        stakeout.save()
    elif action == "enable":
        server = ServerModel.objects(sid=guildid).first()
        server.config["stakeouts"] = 1
        server.save()
    elif action == "disable":
        server = ServerModel.objects(sid=guildid).first()
        server.config["stakeouts"] = 0
        server.save()
    elif action == "category":
        server = ServerModel.objects(sid=guildid).first()
        server.stakeoutconfig["category"] = int(value)
        server.save()

    if request.method == "GET":
        return redirect(f"/bot/stakeouts/{guildid}")
    else:
        return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
