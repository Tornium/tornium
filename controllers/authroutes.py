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

import secrets
import typing

from flask import abort, Blueprint, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, fresh_login_required

import redisdb
import tasks
import tasks.user
import utils
import utils.totp
from models.user import User
from models.usermodel import UserModel

mod = Blueprint("authroutes", __name__)


@mod.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    user: typing.Optional = UserModel.objects(key=request.form["key"]).first()

    if user is None:
        try:
            key_info = tasks.tornget(endpoint="key/?selections=info", key=request.form["key"])
        except utils.TornError as e:
            return utils.handle_torn_error(e)
        except utils.NetworkingError as e:
            return utils.handle_networking_error(e)
        except Exception as e:
            return render_template("errors/error.html", title="Error", error=str(e))

        if "error" in key_info:
            return utils.handle_torn_error(utils.TornError(key_info["error"]["code"], "key/?selections=info"))

        if key_info["access_level"] < 3:
            return (
                render_template(
                    "errors/error.html",
                    title="Bad API Key",
                    error="Only Torn API keys that are full or limited access can currently be used. "
                    "Keys with custom permissions are not currently supported either.",
                ),
                400,
            )

        try:
            torn_user = tasks.tornget(endpoint="user/?selections=profile,discord", key=request.form["key"])
        except utils.TornError as e:
            return utils.handle_torn_error(e)
        except utils.NetworkingError as e:
            return utils.handle_networking_error(e)
        except Exception as e:
            return render_template("errors/error.html", title="Error", error=str(e))

        user: UserModel = UserModel.objects(tid=torn_user["player_id"]).modify(
            upsert=True,
            new=True,
            set__name=torn_user["name"],
            set__level=torn_user["level"],
            set__discord_id=torn_user["discord"]["discordID"] if torn_user["discord"]["discordID"] != "" else 0,
            set__factionid=torn_user["faction"]["faction_id"],
            set__status=torn_user["last_action"]["status"],
            set__last_action=torn_user["last_action"]["timestamp"],
            set__last_refresh=utils.now(),
        )

    if user.security == 0:
        login_user(User(user.tid), remember=True)
    elif user.security == 1:
        if not user.admin:
            return abort(501)

        if user.otp_secret == "":
            return (
                render_template(
                    "errors/error.html",
                    title="Security Error",
                    error="The shared secret for OTP could not be located in the database.",
                ),
                401,
            )

        redis_client = redisdb.get_redis()
        client_token = secrets.token_urlsafe()

        if redis_client.exists(f"tornium:login:{client_token}"):
            return render_template(
                "errors/error.html",
                title="Security Error",
                error="The generated client token already exists. Please try again.",
            )

        redis_client.setnx(f"tornium:login:{client_token}", utils.now())
        redis_client.expire(f"tornium:login:{client_token}", 180)  # Expires after three minutes

        redis_client.setnx(f"tornium:login:{client_token}:tid", user.tid)
        redis_client.expire(f"tornium:login:{client_token}:tid", 180)

        return redirect(f"/login/totp?token={client_token}")
    else:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Security",
                error="The security mode attached to this account is not valid. Please contact the server administrator to "
                "fix this in the database.",
            ),
            500,
        )

    return redirect(url_for("baseroutes.index"))


@mod.route("/login/totp", methods=["GET", "POST"])
def topt_verification():
    if request.method == "GET":
        return (
            render_template("totp.html"),
            200,
            {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"},
        )

    client_token = request.form.get("client-token")
    totp_token = request.form.get("totp-token")

    print(client_token)
    print(totp_token)

    if client_token is None:
        return redirect("/login")

    redis_client = redisdb.get_redis()

    if totp_token is None:
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid")
        return redirect("/login")
    elif redis_client.get(f"tornium:login:{client_token}") is None:
        print("invalid client token")
        return redirect("/login")

    user: typing.Optional[UserModel] = UserModel.objects(
        tid=redis_client.get(f"tornium:login:{client_token}:tid")
    ).first()

    if user is None:
        print("invalid client user")
        return redirect("/login")
    elif not secrets.compare_digest(request.form.get("totp-token"), utils.totp.totp(user.otp_secret)):
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}")

        return (
            render_template(
                "errors/error.html",
                title="Invalid TOTP Code",
                error="The provided TOTP code did not match the one stored on the server.",
            ),
            401,
        )

    login_user(User(redis_client.get(f"tornium:login:{client_token}:tid")), remember=True)
    redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}")

    return redirect(url_for("baseroutes.index"))


@mod.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("baseroutes.index"))
