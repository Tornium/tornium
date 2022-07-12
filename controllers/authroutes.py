# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import Blueprint, request, redirect, render_template, abort, url_for
from flask_login import logout_user, login_user
from honeybadger import honeybadger
from is_safe_url import is_safe_url

from models.user import User
from redisdb import get_redis
import tasks
import utils


mod = Blueprint("authroutes", __name__)


@mod.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    global torn_user

    try:
        key_info = tasks.tornget(
            endpoint="key/?selections=info", key=request.form["key"]
        )
    except utils.TornError as e:
        honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
        return utils.handle_torn_error(e)
    except Exception as e:
        return render_template("errors/error.html", title="Error", message=str(e))
    
    if "error" in key_info:
        return utils.handle_torn_error(key_info["error"]["code"])

    if key_info["access_level"] < 3:
        return render_template(
            "errors/error.html",
            title="Bad API Key",
            message="Only Torn API keys that are full or limited access can currently be used. "
            "Keys with custom permissions are not currently supported either.",
        )

    try:
        torn_user = tasks.tornget(endpoint="user/?selections=", key=request.form["key"])
    except utils.TornError as e:
        honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
        return utils.handle_torn_error(e)
    except Exception as e:
        return render_template("errors/error.html", title="Error", message=str(e))

    user = User(torn_user["player_id"], access=key_info["access_level"])

    if user.key != request.form["key"]:
        user.set_key(request.form["key"])

    user.refresh()
    user.faction_refresh()
    login_user(user, remember=True)
    next = request.args.get("next")

    if next is None or next == "None":
        return redirect(url_for("baseroutes.index"))

    if not get_redis().get("tornium:settings:dev"):
        if not is_safe_url(next, {"torn.deek.sh"}):
            abort(400)
    return redirect(next or url_for("baseroutes.index"))


@mod.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("baseroutes.index"))
