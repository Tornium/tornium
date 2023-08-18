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

import importlib.util
import sys

if sys.version_info < (3, 9):
    raise RuntimeError("This package requires Python 3.9+")

# fmt: off
for module in ("ddtrace"):
    try:
        globals()[f"{module}:loaded"] = bool(importlib.util.find_spec(module))
    except (ValueError, ModuleNotFoundError):
        globals()[f"{module}:loaded"] = False
# fmt: on

if globals().get("ddtrace:loaded") and not hasattr(sys, "_called_from_test"):
    import ddtrace

    ddtrace.config.env = "prod"
    ddtrace.tracer.configure(
        enabled=True,
    )
    ddtrace.patch(logging=True)
    ddtrace.patch_all(flask=True)

import datetime
import logging
import secrets
import time

import flask
from flask_cors import CORS
from flask_login import LoginManager, current_user
from mongoengine import connect
from tornium_commons import Config, rds
from tornium_commons.formatters import commas, rel_time, torn_timestamp

config = Config().load()

if not hasattr(sys, "_called_from_test"):
    connect(
        db="Tornium",
        username=config["username"],
        password=config["password"],
        host=f'mongodb://{config["host"]}',
        connect=False,
    )

import utils

FORMAT = (
    "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] "
    "[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%("
    "dd.span_id)s]- %(message)s"
)

logger = logging.getLogger("server")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="server.log", encoding="utf-8", mode="a")
handler.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(handler)


def init__app():
    from controllers import mod as base_mod
    from controllers.api import mod as api_mod
    from controllers.authroutes import mod as auth_mod
    from controllers.bot import mod as bot_mod
    from controllers.cli import mod as cli_mod
    from controllers.errors import mod as error_mod
    from controllers.faction import mod as faction_mod
    from controllers.statroutes import mod as stat_mod
    from controllers.torn import mod as torn_mod
    from skynet import mod as skynet_mod

    app = flask.Flask(__name__)
    if config["secret"] is None:
        app.secret_key = config.regen_secret()
    else:
        app.secret_key = config["secret"]

    app.config["REMEMBER_COOKIE_DURATION"] = 604800
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    CORS(
        app,
        resources={
            r"/api/*": {"origins": "*"},
            r"/*": {"origins": config["domain"]},
        },
        supports_credentials=True,
    )

    login_manager.init_app(app)
    login_manager.login_view = "authroutes.login"
    login_manager.refresh_view = "authroutes.login"
    login_manager.session_protection = "strong"
    login_manager.login_message = ""
    login_manager.message = ""

    tornium_ext: utils.tornium_ext.TorniumExt
    for tornium_ext in utils.tornium_ext.TorniumExt.__iter__():
        logger.info(f"Initializing Tornium extension {tornium_ext.name}")
        tornium_ext.extension.init_app(app)

    with app.app_context():
        app.register_blueprint(base_mod)
        app.register_blueprint(auth_mod)
        app.register_blueprint(faction_mod)
        app.register_blueprint(bot_mod)
        app.register_blueprint(error_mod)
        app.register_blueprint(stat_mod)
        app.register_blueprint(api_mod)
        app.register_blueprint(torn_mod)
        app.register_blueprint(skynet_mod)
        app.register_blueprint(cli_mod)

    return app


login_manager = LoginManager()
app = init__app()


@login_manager.user_loader
def load_user(user_id):
    from models.user import User

    return User(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    if flask.request.blueprint == "api":
        flask.abort(401)

    flask.session["next"] = flask.request.url
    return flask.redirect(flask.url_for(login_manager.login_view))


@login_manager.needs_refresh_handler
def refresh_needed():
    if flask.request.blueprint == "api":
        flask.abort(401)

    flask.session["next"] = flask.request.url
    return flask.redirect(flask.url_for(login_manager.refresh_view))


@app.template_filter("reltime")
def relative_time(s):
    return rel_time(datetime.datetime.fromtimestamp(s))


@app.template_filter("tcttime")
def tct_time(s):
    return torn_timestamp(int(s))


@app.template_filter("commas")
def commas_filter(s):
    return commas(int(s))


@app.before_request
def before_request():
    flask.session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=31)

    if globals().get("ddtrace:loaded") is None:
        try:
            import ddtrace

            globals()["ddtrace:loaded"] = True
        except (ImportError, ModuleNotFoundError):
            globals()["ddtrace:loaded"] = False

    if globals().get("ddtrace:loaded") and current_user.is_authenticated:
        import ddtrace  # noqa

        ddtrace.tracer.current_root_span().set_tag("user_id", current_user.tid)


@app.after_request
def after_request(response: flask.Response):
    # HSTS enabled through CloudFlare
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy
    # response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # X-Content-Type-Options
    response.headers["X-Content-Type-Options"] = "nosniff"

    # X-Frame-Options
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    if current_user.is_authenticated:
        api_token = flask.request.cookies.get("token")

        if api_token is None:
            redis_client = rds()
            client_token = secrets.token_urlsafe()

            redis_client.set(
                f"tornium:token:api:{client_token}", f"{int(time.time())}|{current_user.tid}", nx=True, ex=300
            )

            response.set_cookie("token", client_token, max_age=300, secure=True, httponly=True, samesite="Strict")

    return response
