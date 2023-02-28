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

import hashlib
import secrets
import typing

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user, fresh_login_required

import redisdb
import tasks
import tasks.user
import utils
import utils.totp
from controllers.api.utils import json_api_exception
from controllers.decorators import token_required
from models.user import User
from models.usermodel import UserModel

mod = Blueprint("authroutes", __name__)


@mod.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    user: typing.Optional[UserModel] = UserModel.objects(key=request.form["key"]).first()

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

    tasks.user.update_user(key=request.form["key"], tid=0, refresh_existing=True)

    user: typing.Optional[UserModel] = UserModel.objects(key=request.form["key"]).first()

    if user is None:
        return render_template(
            "errors/error.html",
            title="User Not Found",
            error="Even after an update, the user and their key could not be located in the database. Please contact "
            "tiksan [2383326] for support.",
        )

    if user.security == 0:
        login_user(User(user.tid), remember=True)
    elif user.security == 1:
        if user.otp_secret == "":  # nosec B105
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

    if client_token is None:
        return redirect("/login")

    redis_client = redisdb.get_redis()

    if totp_token is None:
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid")
        return redirect("/login")
    elif redis_client.get(f"tornium:login:{client_token}") is None:
        return redirect("/login")

    user: typing.Optional[UserModel] = UserModel.objects(
        tid=redis_client.get(f"tornium:login:{client_token}:tid")
    ).first()

    if user is None:
        return redirect("/login")

    server_totp_tokens = utils.totp.totp(user.otp_secret)

    if secrets.compare_digest(totp_token, server_totp_tokens[0]) or secrets.compare_digest(
        totp_token, server_totp_tokens[1]
    ):
        login_user(User(redis_client.get(f"tornium:login:{client_token}:tid")), remember=True)
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid")
        return redirect(url_for("baseroutes.index"))
    elif hashlib.sha256(totp_token.encode("utf-8")).hexdigest() in user.otp_backups:
        user.otp_backups.remove(hashlib.sha256(totp_token.encode("utf-8")).hexdigest())
        user.save()

        login_user(User(redis_client.get(f"tornium:login:{client_token}:tid")), remember=True)
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid")
        return redirect(url_for("baseroutes.index"))
    else:
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid")

        return (
            render_template(
                "errors/error.html",
                title="Invalid TOTP Code",
                error="The provided TOTP code did not match the one stored on the server.",
            ),
            401,
        )


@mod.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("baseroutes.index"))


@mod.route("/totp/secret", methods=["GET"])
@fresh_login_required
@token_required(setnx=False)
def totp_secret(*args, **kwargs):
    return {
        "secret": current_user.otp_secret,
        "url": current_user.generate_otp_url(),
    }, 200


@mod.route("/totp/secret", methods=["POST"])
@fresh_login_required
@token_required(setnx=False)
def totp_secret_regen(*args, **kwargs):
    current_user.generate_otp_secret()
    response = json_api_exception("0001")

    return {
        "code": response["code"],
        "name": response["name"],
        "message": response["message"],
    }, 200


@mod.route("/totp/backup", methods=["POST"])
@fresh_login_required
@token_required(setnx=False)
def totp_backup_regen(*args, **kwargs):
    codes = current_user.generate_otp_backups()

    return {"codes": codes}, 200


@mod.route("/security", methods=["POST"])
@fresh_login_required
@token_required(setnx=False)
def set_security_mode(*args, **kwargs):
    mode = request.args.get("mode")

    if mode not in (0, 1):
        response = json_api_exception("1000", details={"message": "Invalid security mode"})

        return {
            "code": response["code"],
            "name": response["name"],
            "message": response["message"],
            "details": response["details"],
        }, 400

    user: UserModel = UserModel.objects(tid=current_user.tid).first()
    user.security = mode
    user.save()

    response = json_api_exception("0001")

    return {
        "code": response["code"],
        "name": response["name"],
        "message": response["message"],
    }, 200
