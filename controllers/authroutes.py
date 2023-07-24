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

import datetime
import hashlib
import inspect
import json
import random
import secrets
import time
import typing

import celery.exceptions
import requests
from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import (
    current_user,
    fresh_login_required,
    login_required,
    login_user,
    logout_user,
)
from mongoengine import QuerySet
from tornium_celery.tasks.api import tornget
from tornium_celery.tasks.misc import send_dm
from tornium_celery.tasks.user import update_user
from tornium_commons import Config, rds
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.models import UserModel
from tornium_commons.skyutils import SKYNET_INFO

import utils
import utils.totp
from controllers.api.utils import json_api_exception
from controllers.decorators import token_required
from models.user import User

mod = Blueprint("authroutes", __name__)


@mod.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session["oauth_state"] = secrets.token_urlsafe()

        return render_template("login.html")

    user: typing.Optional[UserModel] = UserModel.objects(key=request.form["key"]).first()

    if user is None:
        try:
            key_info = tornget(endpoint="key/?selections=info", key=request.form["key"])
        except TornError as e:
            return utils.handle_torn_error(e)
        except NetworkingError as e:
            return utils.handle_networking_error(e)
        except Exception as e:
            return render_template("errors/error.html", title="Error", error=str(e))

        if "error" in key_info:
            return utils.handle_torn_error(TornError(key_info["error"]["code"], "key/?selections=info"))

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
        update_user(key=request.form["key"], tid=0, refresh_existing=False).get()
    except celery.exceptions.TimeoutError:
        return render_template(
            "errors/error.html",
            title="Timeout",
            error="The Torn API or Celery backend has timed out on your API calls. Please try again.",
        )
    except NetworkingError as e:
        return utils.handle_torn_error(e)
    except TornError as e:
        return utils.handle_torn_error(e)
    except AttributeError:
        pass

    user: typing.Optional[UserModel] = UserModel.objects(key=request.form["key"]).no_cache().first()

    if user is None:
        return render_template(
            "errors/error.html",
            title="User Not Found",
            error="Even after an update, the user and their key could not be located in the database. Please try "
            "again and if this problem persists, contact tiksan [2383326] for support.",
        )

    if not current_user.is_authenticated and user.discord_id not in (0, None, ""):
        discord_payload = {
            "embeds": [
                {
                    "title": "Security Alert",
                    "description": inspect.cleandoc(
                        f"""Someone has signed into your Tornium account from {request.headers.get("CF-Connecting-IP")} [{request.headers.get("CF-IPCountry")}] <t:{int(datetime.datetime.utcnow().timestamp())}:R>.

                        If this was not you, please contact the developer as soon as possible. You may need to reset your API key to secure your account.

                        WARNING: If the developer is accessing your Tornium account, they will contact you ahead of time through the linked Discord account."""
                    ),
                    "color": SKYNET_INFO,
                }
            ],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 5,
                            "label": "tiksan [2383326] @ Discord (preferred)",
                            "url": "https://discord.com/users/695828257949352028",
                        }
                    ],
                },
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 5,
                            "label": "tiksan [2383326] @ Torn",
                            "url": "https://www.torn.com/profiles.php?XID=2383326",
                        },
                    ],
                },
            ],
        }

        send_dm.delay(user.discord_id, discord_payload).forget()

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

        redis_client = rds()
        client_token = secrets.token_urlsafe()

        if redis_client.exists(f"tornium:login:{client_token}"):
            return render_template(
                "errors/error.html",
                title="Security Error",
                error="The generated client token already exists. Please try again.",
            )

        redis_client.setnx(f"tornium:login:{client_token}", time.time())
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

    if session.get("next") is None:
        return redirect(url_for("baseroutes.index"))
    else:
        return redirect(session.get("next"))


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

    redis_client = rds()

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

        if session.get("next") is None:
            return redirect(url_for("baseroutes.index"))
        else:
            return redirect(session.get("next"))
    elif hashlib.sha256(totp_token.encode("utf-8")).hexdigest() in user.otp_backups:
        user.otp_backups.remove(hashlib.sha256(totp_token.encode("utf-8")).hexdigest())
        user.save()

        login_user(User(redis_client.get(f"tornium:login:{client_token}:tid")), remember=True)
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid")

        if session.get("next") is None:
            return redirect(url_for("baseroutes.index"))
        else:
            return redirect(session.get("next"))
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


@mod.route("/login/skynet", methods=["GET"])
def skynet_login():
    # See https://discord.com/developers/docs/topics/oauth2#authorization-code-grant

    d_code = request.args.get("code")
    oauth_state = request.args.get("state")

    if oauth_state != session.get("oauth_state"):
        session.pop("oauth_state", None)
        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. No state code was included in the Discord callback or in the session. Please "
                "try again and make sure that you're on the correct website.",
            ),
            401,
        )

    payload = {
        "client_id": Config()["skynet-applicationid"],
        "client_secret": Config()["skynet-client-secret"],
        "grant_type": "authorization_code",
        "code": d_code,
        "redirect_uri": "https://tornium.com/login/skynet",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    access_token_data = requests.post(
        "https://discord.com/api/v10/oauth2/token", headers=headers, data=payload, timeout=5
    )
    access_token_data.raise_for_status()
    access_token_json = access_token_data.json()

    headers = {
        "Authorization": f"Bearer {access_token_json['access_token']}",
        "Content-Type": "application/json",
    }

    user_request = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=5)
    user_request.raise_for_status()
    user_data = user_request.json()
    print(user_data)

    user_qs: QuerySet = UserModel.objects(discord_id=user_data["id"])
    user: typing.Optional[UserModel] = user_qs.first()

    if user is None:
        try:
            update_user(
                key=random.choice(UserModel.objects(key__nin=[None, ""])),
                discordid=user_data["id"],
                refresh_existing=False,
            ).get()
        except celery.exceptions.TimeoutError:
            return render_template(
                "errors/error.html",
                title="Timeout",
                error="The Torn API or Celery backend has timed out on your API calls. Please try again.",
            )
        except NetworkingError as e:
            return utils.handle_torn_error(e)
        except TornError as e:
            return utils.handle_torn_error(e)

        user = UserModel.objects(discord_id=user_data["id"]).first()

        if user is None:
            return render_template(
                "errors/error.html",
                title="User Not Found",
                error="Even after an update, the user and their key could not be located in the database. Please try "
                "again and if this problem persists, contact tiksan [2383326] for support.",
            )

        # Skip security alert as an alert to a compromised Discord account is useless

    # Skip 2FA for now as it is assumed that Discord SSO is more secure than a Torn API key
    # Especially if 2FA is already enabled on Discord for the user

    login_user(User(user.tid), remember=True)

    if session.get("next") is None:
        return redirect(url_for("baseroutes.index"))
    else:
        return redirect(session.get("next"))


@mod.route("/login/skynet/callback", methods=["POST"])
def skynet_login_callback():
    data = json.loads(request.get_data().decode("utf-8"))
    print(data)

    return data


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
    data = json.loads(request.get_data().decode("utf-8"))
    mode = data.get("mode")

    # TODO: Generate OTP secret if not created upon enable

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
