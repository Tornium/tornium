# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import hashlib
import inspect
import secrets
import time
import typing
from functools import wraps

import requests
from flask import (
    Blueprint,
    Response,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from peewee import DataError, DoesNotExist
from tornium_celery.tasks.api import tornget
from tornium_celery.tasks.misc import send_dm
from tornium_celery.tasks.user import update_user
from tornium_commons import Config, rds
from tornium_commons.errors import (
    DiscordError,
    MissingKeyError,
    NetworkingError,
    TornError,
)
from tornium_commons.formatters import rel_time
from tornium_commons.models import AuthAction, AuthLog, TornKey, User
from tornium_commons.skyutils import SKYNET_INFO

import utils
import utils.totp
from models.user import AuthUser

mod = Blueprint("authroutes", __name__)
config = Config.from_json()


def _log_auth(
    user: typing.Optional[int],
    action: AuthAction,
    login_key: typing.Optional[str] = None,
    details: typing.Optional[str] = None,
):
    try:
        AuthLog.insert(
            user=user,
            timestamp=datetime.datetime.utcnow(),
            ip=request.headers.get("CF-Connecting-IP") or request.remote_addr,
            action=action.value,
            login_key=login_key,
            details=details,
        ).execute()
    except DataError:
        # Some IP addresses are larger than the data field
        AuthLog.insert(
            user=user,
            timestamp=datetime.datetime.utcnow(),
            ip=None,
            action=action.value,
            login_key=login_key,
            details=details,
        ).execute()


def disable_cache(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        response: Response = make_response(f(*args, **kwargs))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response

    return wrapper


def _increment_ratelimit(ratelimit_key):
    redis_client = rds()
    failed_attempt_count = redis_client.incr(ratelimit_key)
    redis_client.expire(ratelimit_key, max(10, 2**failed_attempt_count))


@mod.route("/login", methods=["GET", "POST"])
@disable_cache
def login(*args, **kwargs):
    redis_client = rds()
    ip_addr = request.headers.get("CF-Connecting-IP") or request.remote_addr
    ratelimit_key = f"tornium:login-ratelimit:{ip_addr}"

    if redis_client.exists(ratelimit_key):
        ratelimit_ttl = redis_client.ttl(ratelimit_key)
        _increment_ratelimit(ratelimit_key)
        return (
            render_template(
                "errors/error.html",
                title="Too Many Requests",
                error=f"Security error. Too many requests. Try again in {rel_time(int(time.time()) + ratelimit_ttl)}.",
            ),
            429,
        )

    if request.method == "GET":
        session["oauth_state"] = secrets.token_urlsafe()
        return render_template("login.html")

    session_oauth_state = session.pop("oauth_state", None)
    oauth_state = request.args.get("state")

    if oauth_state is None:
        _log_auth(user=None, action=AuthAction.LOGIN_TORN_API_FAILED, details="OAuth state mismatch")
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. No state code was included in the request. Please try again and make sure that you're on the correct website.",
            ),
            401,
        )
    elif session_oauth_state is None:
        _log_auth(user=None, action=AuthAction.LOGIN_TORN_API_FAILED, details="OAuth session state mismatch")
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. No state code was included in the session. Please try again and make sure that you're on the correct website.",
            ),
            401,
        )
    elif oauth_state != session_oauth_state:
        _log_auth(user=None, action=AuthAction.LOGIN_TORN_API_FAILED, details="OAuth state mismatch")
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. An invalid state code was included in the request. Please "
                "try again and make sure that you're on the correct website.",
            ),
            401,
        )

    if request.form.get("key") is None or len(request.form["key"]) != 16:
        _log_auth(
            user=None,
            action=AuthAction.LOGIN_TORN_API_FAILED,
            login_key=request.form.get("key"),
            details="Invalid API key",
        )
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Invalid API Key",
                error="Torn API keys must be 16 characters in length. Please make sure that you're using the correct "
                "API key (e.g. Torn Stats API keys will not work).",
            ),
            400,
        )

    user: typing.Optional[User]
    try:
        user = TornKey.select(TornKey.user).where(TornKey.api_key == request.form["key"]).get().user
    except DoesNotExist:
        user = None

    if user is None:
        try:
            key_info = tornget(endpoint="key/?selections=info", key=request.form["key"])
        except TornError as e:
            _log_auth(
                user=None,
                action=AuthAction.LOGIN_TORN_API_FAILED,
                login_key=request.form.get("key"),
                details="Invalid API key",
            )
            _increment_ratelimit(ratelimit_key)

            return utils.handle_torn_error(e), 401
        except NetworkingError as e:
            _log_auth(
                user=None,
                action=AuthAction.LOGIN_TORN_API_FAILED,
                login_key=request.form.get("key"),
                details=f"Torn networking error ({e.code})",
            )
            _increment_ratelimit(ratelimit_key)

            return utils.handle_networking_error(e), 502
        except Exception as e:
            _log_auth(user=None, action=AuthAction.LOGIN_TORN_API_FAILED, login_key=request.form.get("key"))
            _increment_ratelimit(ratelimit_key)

            return (
                render_template("errors/error.html", title="Error", error=str(e)),
                500,
            )

        if key_info["access_level"] < 3:
            # TODO: Allow all API keys but determine how they're marked as default
            _log_auth(
                user=None,
                action=AuthAction.LOGIN_TORN_API_FAILED,
                login_key=request.form.get("key"),
                details="Key access level too low",
            )
            _increment_ratelimit(ratelimit_key)

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
        update_user(key=request.form["key"], tid=0, refresh_existing=False)
    except NetworkingError as e:
        _log_auth(
            user=None,
            action=AuthAction.LOGIN_TORN_API_FAILED,
            login_key=request.form.get("key"),
            details=f"Torn networking error ({e.code})",
        )
        _increment_ratelimit(ratelimit_key)

        return utils.handle_networking_error(e)
    except TornError as e:
        _log_auth(
            user=None,
            action=AuthAction.LOGIN_TORN_API_FAILED,
            login_key=request.form.get("key"),
            details=f"Torn API error ({e.code})",
        )
        _increment_ratelimit(ratelimit_key)

        return utils.handle_torn_error(e)

    try:
        user = TornKey.select(TornKey.user).where(TornKey.api_key == request.form["key"]).get().user
    except DoesNotExist:
        _log_auth(user=None, action=AuthAction.LOGIN_TORN_API_FAILED, login_key=request.form.get("key"))
        _increment_ratelimit(ratelimit_key)

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
                        f"""Someone has signed into your Tornium account (ID {user.tid}) from {request.headers.get("CF-Connecting-IP") or request.remote_addr} [{request.headers.get("CF-IPCountry")}] <t:{int(time.time())}:R>.

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
                            "label": "tiksan [2383326] @ Torn (preferred)",
                            "url": "https://www.torn.com/profiles.php?XID=2383326",
                        },
                    ],
                },
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 5,
                            "label": "tiksan [2383326] @ Discord",
                            "url": "https://discord.com/users/695828257949352028",
                        }
                    ],
                },
            ],
        }

        send_dm.delay(user.discord_id, discord_payload).forget()

    if user.security == 0 or user.security is None:
        # TODO: Make the key query above the same as the query required for login
        auth_user: AuthUser = (
            AuthUser.select(
                AuthUser.tid,
            )
            .where(AuthUser.tid == user.tid)
            .get()
        )
        _log_auth(user=auth_user.tid, action=AuthAction.LOGIN_TORN_API_SUCCESS, login_key=request.form.get("key"))
        redis_client.delete(ratelimit_key)

        login_user(auth_user, remember=True)
    elif user.security == 1:
        _log_auth(user=user.tid, action=AuthAction.LOGIN_TORN_API_PARTIAL, login_key=request.form.get("key"))

        if user.otp_secret == "":  # nosec B105
            _log_auth(
                user=user.tid,
                action=AuthAction.LOGIN_TOTP_FAILED,
                login_key=request.form.get("key"),
                details="No OTP secret stored",
            )
            _increment_ratelimit(ratelimit_key)

            return (
                render_template(
                    "errors/error.html",
                    title="Security Error",
                    error="The shared secret for OTP could not be located in the database. Please contact tiksan [2383326] on Torn to resolve this.",
                ),
                401,
            )

        client_token = secrets.token_urlsafe()

        if not rds().set(f"tornium:login:{client_token}", user.tid, nx=True, ex=180):
            _log_auth(
                user=user.tid,
                action=AuthAction.LOGIN_TOTP_FAILED,
                login_key=request.form.get("key"),
                details="Duplicate client token",
            )
            _increment_ratelimit(ratelimit_key)

            return (
                render_template(
                    "errors/error.html",
                    title="Security Error",
                    error="The generated client token already exists. Please try again.",
                ),
                500,
            )

        return redirect(f"/login/totp?token={client_token}")
    else:
        _log_auth(
            user=user.tid,
            action=AuthAction.LOGIN_FAILED,
            login_key=request.form.get("key"),
            details="Unknown security mode",
        )
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Unknown Security",
                error="The security mode attached to this account is not valid. Please contact the server "
                "administrator to fix this in the database.",
            ),
            500,
        )

    next_route = session.pop("next", None)
    return redirect(next_route or url_for("baseroutes.index"))


@mod.route("/login/totp", methods=["GET", "POST"])
@disable_cache
def topt_verification():
    redis_client = rds()
    ip_addr = request.headers.get("CF-Connecting-IP") or request.remote_addr
    ratelimit_key = f"tornium:login-ratelimit:{ip_addr}"

    if redis_client.exists(ratelimit_key):
        ratelimit_ttl = redis_client.ttl(ratelimit_key)
        _increment_ratelimit(ratelimit_key)
        return (
            render_template(
                "errors/error.html",
                title="Too Many Requests",
                error=f"Security error. Too many requests. Try again in {rel_time(int(time.time()) + ratelimit_ttl)}.",
            ),
            429,
        )

    if request.method == "GET":
        return (render_template("totp.html"), 200)

    client_token = request.form.get("client-token")
    totp_token = request.form.get("totp-token")

    if client_token is None:
        _log_auth(user=None, action=AuthAction.LOGIN_TOTP_FAILED, details="Invalid client token")
        _increment_ratelimit(ratelimit_key)

        return redirect("/login")

    redis_client = rds()

    if totp_token is None:
        _log_auth(user=None, action=AuthAction.LOGIN_TOTP_FAILED, details="Invalid TOTP token")
        _increment_ratelimit(ratelimit_key)

        redis_client.delete(f"tornium:login:{client_token}")
        return redirect("/login")

    user_id: typing.Optional[str] = redis_client.get(f"tornium:login:{client_token}")

    try:
        # TODO: Select only the necessary fields in this query
        user: AuthUser = AuthUser.get_by_id(int(user_id))
    except (TypeError, ValueError, DoesNotExist):
        _log_auth(user=None, action=AuthAction.LOGIN_TOTP_FAILED)
        _increment_ratelimit(ratelimit_key)

        return redirect("/login")

    server_totp_tokens = utils.totp.totp(user.otp_secret)
    next_route = session.pop("next", None)

    if secrets.compare_digest(totp_token, server_totp_tokens[0]) or secrets.compare_digest(
        totp_token, server_totp_tokens[1]
    ):
        login_user(user, remember=True)
        _log_auth(user=user.tid, action=AuthAction.LOGIN_TOTP_SUCCESS)
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid", ratelimit_key)

        return redirect(next_route or url_for("baseroutes.index"))
    elif hashlib.sha256(totp_token.encode("utf-8")).hexdigest() in user.otp_backups:
        user.otp_backups.remove(hashlib.sha256(totp_token.encode("utf-8")).hexdigest())
        User.update(otp_backups=user.otp_backups).where(User.tid == user.tid).execute()

        login_user(user, remember=True)
        _log_auth(user=user.tid, action=AuthAction.LOGIN_TOTP_SUCCESS, details="Backup code used")
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid", ratelimit_key)

        return redirect(next_route or url_for("baseroutes.index"))
    else:
        redis_client.delete(f"tornium:login:{client_token}", f"tornium:login:{client_token}:tid")
        _log_auth(
            user=user.tid, action=AuthAction.LOGIN_TOTP_FAILED, login_key=str(totp_token), details="Invalid TOTP token"
        )
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Invalid TOTP Code",
                error="The provided TOTP code did not match the one stored on the server.",
            ),
            401,
        )


@mod.route("/login/discord", methods=["GET"])
@disable_cache
def discord_login():
    redis_client = rds()
    ip_addr = request.headers.get("CF-Connecting-IP") or request.remote_addr
    ratelimit_key = f"tornium:login-ratelimit:{ip_addr}"

    if redis_client.exists(ratelimit_key):
        ratelimit_ttl = redis_client.ttl(ratelimit_key)
        _increment_ratelimit(ratelimit_key)
        return (
            render_template(
                "errors/error.html",
                title="Too Many Requests",
                error=f"Security error. Too many requests. Try again in {rel_time(int(time.time()) + ratelimit_ttl)}.",
            ),
            429,
        )

    # See https://discord.com/developers/docs/topics/oauth2#authorization-code-grant
    session_oauth_state = session.pop("oauth_state", None)

    if request.args.get("error") is not None:
        _log_auth(user=None, action=AuthAction.LOGIN_DISCORD_FAILED, details=request.args["errors"])
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title=request.args["errors"],
                error=request.args.get("error_description"),
            ),
            400,
        )

    d_code = request.args.get("code")
    oauth_state = request.args.get("state")

    if oauth_state is None:
        _log_auth(user=None, action=AuthAction.LOGIN_DISCORD_FAILED, details="OAuth state mismatch")
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. No state code was included in the Discord callback. Please try again and make sure that you're on the correct website.",
            ),
            401,
        )
    elif session_oauth_state is None:
        _log_auth(user=None, action=AuthAction.LOGIN_DISCORD_FAILED, details="OAuth session state mismatch")
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. No state code was included in the session. Please try again and make sure that you're on the correct website.",
            ),
            401,
        )
    elif oauth_state != session_oauth_state:
        _log_auth(user=None, action=AuthAction.LOGIN_DISCORD_FAILED, details="OAuth state mismatch")
        _increment_ratelimit(ratelimit_key)

        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. An invalid state code was included in the request. Please "
                "try again and make sure that you're on the correct website.",
            ),
            401,
        )

    payload = {
        "client_id": config.bot_application_id,
        "client_secret": config.bot_client_secret,
        "grant_type": "authorization_code",
        "code": d_code,
        "redirect_uri": "https://tornium.com/login/discord",
    }
    access_token_data = requests.post(
        "https://discord.com/api/v10/oauth2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=payload,
        timeout=10,
    )
    try:
        access_token_json = access_token_data.json()
    except requests.exceptions.JSONDecodeError:
        return (
            render_template(
                "errors/error.html",
                title="Internal Error",
                error="Internal error. Discord failed to respond with a valid token response.",
            ),
            500,
        )

    if "error" in access_token_json:
        return render_template(
            "errors/error.html",
            title=f"OAuth Error | {access_token_json['error']}",
            error=f"Discord failed to create an OAuth token. {access_token_json.get('error_description', 'MISSING ERROR DESCRIPTION')}",
        )

    user_request = requests.get(
        "https://discord.com/api/v10/users/@me",
        headers={
            "Authorization": f"Bearer {access_token_json['access_token']}",
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    try:
        user_data = user_request.json()
    except requests.exceptions.JSONDecodeError:
        return (
            render_template(
                "errors/error.html",
                title="Internal Error",
                error="Internal error. Discord failed to respond with a valid user response.",
            ),
            500,
        )

    if "code" in user_data:
        raise DiscordError(code=user_data["code"], message=user_data["message"], url="users/@me")

    # TODO: Limit selected fields in this query
    user: typing.Optional[AuthUser] = AuthUser.select().where(AuthUser.discord_id == user_data["id"]).first()

    if user is None:
        try:
            update_user(
                key=TornKey.random_key(),
                discordid=user_data["id"],
                refresh_existing=False,
            )
        except NetworkingError as e:
            _log_auth(user=None, action=AuthAction.LOGIN_DISCORD_FAILED, details=f"Torn networking error ({e.code})")
            _increment_ratelimit(ratelimit_key)

            return utils.handle_networking_error(e)
        except TornError as e:
            _log_auth(user=None, action=AuthAction.LOGIN_DISCORD_FAILED, details=f"Torn API error ({e.code})")
            _increment_ratelimit(ratelimit_key)

            return utils.handle_torn_error(e)
        except MissingKeyError:
            _log_auth(user=None, action=AuthAction.LOGIN_DISCORD_FAILED)
            _increment_ratelimit(ratelimit_key)

            return (
                render_template(
                    "errors/error.html",
                    title="Internal Error",
                    error="No API keys were available to update your user data. Please contact the server admin.",
                ),
                500,
            )

        try:
            user = AuthUser.get(AuthUser.discord_id == user_data["id"])
        except DoesNotExist:
            return render_template(
                "errors/error.html",
                title="User Not Found",
                error="Even after an update, the user could not be located in the database. Please try again and if "
                "this problem persists, contact tiksan [2383326] for support.",
            )

        # Skip security alert as an alert to a compromised Discord account is useless
        pass

    if user.security == 0 or user.security is None:
        _log_auth(user=user.tid, action=AuthAction.LOGIN_DISCORD_SUCCESS, login_key=user_data["id"])
        redis_client.delete(ratelimit_key)

        login_user(user, remember=True)
    elif user.security == 1:
        _log_auth(user=user.tid, action=AuthAction.LOGIN_DISCORD_PARTIAL, login_key=user_data["id"])

        if user.otp_secret == "":  # nosec B105
            _log_auth(
                user=user.tid,
                action=AuthAction.LOGIN_TOTP_FAILED,
                login_key=user_data["id"],
                details="No OTP secret stored",
            )
            _increment_ratelimit(ratelimit_key)

            return (
                render_template(
                    "errors/error.html",
                    title="Security Error",
                    error="The shared secret for OTP could not be located in the database. Please contact tiksan [2383326] on Torn to resolve this.",
                ),
                401,
            )

        client_token = secrets.token_urlsafe()

        if not rds().set(f"tornium:login:{client_token}", user.tid, nx=True, ex=180):
            _log_auth(
                user=user.tid,
                action=AuthAction.LOGIN_TOTP_FAILED,
                login_key=user_data["id"],
                details="Duplicate client token",
            )
            _increment_ratelimit(ratelimit_key)

            return (
                render_template(
                    "errors/error.html",
                    title="Security Error",
                    error="The generated client token already exists. Please try again.",
                ),
                500,
            )

        return redirect(f"/login/totp?token={client_token}")
    else:
        _log_auth(
            user=user.tid, action=AuthAction.LOGIN_FAILED, login_key=user_data["id"], details="Unknown security mode"
        )

        return (
            render_template(
                "errors/error.html",
                title="Unknown Security",
                error="The security mode attached to this account is not valid. Please contact the server "
                "administrator to fix this in the database.",
            ),
            500,
        )

    next_route = session.pop("next", None)
    return redirect(next_route or url_for("baseroutes.index"))


@mod.route("/logout", methods=["POST"])
@login_required
@disable_cache
def logout():
    logout_token = session.pop("logout_token", None)
    state = request.args.get("state")

    if state is None:
        _log_auth(user=current_user.tid, action=AuthAction.LOGOUT_FAILED, details="Logout state mismatch")

        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. No state code was included while logging out. Please try again and make sure that you're on the correct website.",
            ),
            401,
        )
    elif state != logout_token:
        _log_auth(user=current_user.tid, action=AuthAction.LOGOUT_FAILED, details="Logout state mismatch")

        return (
            render_template(
                "errors/error.html",
                title="Unauthorized",
                error="Security error. An invalid state code was included in the Discord callback or in the session. Please "
                "try again and make sure that you're on the correct website.",
            ),
            401,
        )

    _log_auth(user=current_user.tid, action=AuthAction.LOGOUT_SUCESS)
    logout_user()

    # Remove/invalidate security-related tokens for the session for additional security
    session.pop("csrf_token", None)

    return redirect(url_for("baseroutes.index"))
