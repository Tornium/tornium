# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import Blueprint, request, redirect, render_template, url_for
from flask_login import logout_user, login_user

from models.user import User
import tasks
import utils


mod = Blueprint("authroutes", __name__)


@mod.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    global torn_user

    try:
        key_info = tasks.tornget(endpoint="key/?selections=info", key=request.form["key"])
    except utils.TornError as e:
        return utils.handle_torn_error(e)
    except Exception as e:
        return render_template("errors/error.html", title="Error", message=str(e))

    if "error" in key_info:
        return utils.handle_torn_error(utils.TornError(key_info["error"]["code"], "key/?selections=info"))

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
        return utils.handle_torn_error(e)
    except Exception as e:
        return render_template("errors/error.html", title="Error", message=str(e))

    user = User(torn_user["player_id"])

    if user.key != request.form["key"]:
        user.set_key(request.form["key"])

    try:
        user.refresh()
        user.faction_refresh()
    except utils.TornError as e:
        return utils.handle_torn_error(e)
    except utils.NetworkingError as e:
        if e.code == 408:
            return render_template(
                "errors/error.html",
                title="Torn API Timeout",
                message="The Torn API has taken too long to respond to the API request. Please try again.",
            )

        return render_template("errors/error.html", title="Networking Error", message=e.message)

    login_user(user, remember=True)

    return redirect(url_for("baseroutes.index"))


@mod.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("baseroutes.index"))
