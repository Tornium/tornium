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

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_user, logout_user

import tasks
import utils
from models.user import User

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
    except utils.NetworkingError as e:
        return utils.handle_networking_error(e)
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
    except utils.NetworkingError as e:
        return utils.handle_networking_error(e)
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
