# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import ddtrace

ddtrace.config.env = "prod"
ddtrace.tracer.configure(
    enabled=True,
)
ddtrace.patch(logging=True)
ddtrace.patch_all(flask=True)

import datetime
import logging

import flask
from flask_cors import CORS
from flask_login import LoginManager
from mongoengine import connect

import settings  # Do not remove - initializes redis values
from redisdb import get_redis


redis = get_redis()

connect(
    db="Tornium",
    username=redis.get("tornium:settings:username"),
    password=redis.get("tornium:settings:password"),
    host=f'mongodb://{redis.get("tornium:settings:host")}',
    connect=False,
)

from controllers import mod as base_mod
from controllers.authroutes import mod as auth_mod
from controllers.faction import mod as faction_mod
from controllers.bot import mod as bot_mod
from controllers.errors import mod as error_mod
from controllers.adminroutes import mod as admin_mod
from controllers.statroutes import mod as stat_mod
from controllers.api import mod as api_mod
from controllers.torn import mod as torn_mod
from skynet import mod as skynet_mod
import utils

FORMAT = (
    "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] "
    "[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] "
    "- %(message)s"
)

logger = logging.getLogger("server")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="server.log", encoding="utf-8", mode="a")
handler.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(handler)

app = flask.Flask(__name__)
app.secret_key = redis.get("tornium:settings:secret")
app.config["REMEMBER_COOKIE_DURATION"] = 604800

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "authroutes.login"
login_manager.refresh_view = "authroutes.login"
login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id):
    from models.user import User

    return User(user_id)


@app.template_filter("reltime")
def relative_time(s):
    return utils.rel_time(datetime.datetime.fromtimestamp(s))


@app.template_filter("tcttime")
def tct_time(s):
    return utils.torn_timestamp(int(s))


@app.template_filter("commas")
def commas(s):
    return utils.commas(int(s))


@app.before_request
def before_request():
    flask.session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=31)


@app.after_request
def after_request(response: flask.Response):
    # HSTS enabled through CloudFlare
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy

    # X-Content-Type-Options
    response.headers["X-Content-Type-Options"] = "nosniff"

    # X-Frame-Options
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    return response


if redis.get("tornium:settings:dev") == "True" and __name__ == "__main__":
    app.register_blueprint(base_mod)
    app.register_blueprint(auth_mod)
    app.register_blueprint(faction_mod)
    app.register_blueprint(bot_mod)
    app.register_blueprint(error_mod)
    app.register_blueprint(admin_mod)
    app.register_blueprint(stat_mod)
    app.register_blueprint(api_mod)
    app.register_blueprint(torn_mod)
    app.register_blueprint(skynet_mod)

    app.run("localhost", 8000, debug=True)

if redis.get("tornium:settings:dev") == "False":
    app.register_blueprint(base_mod)
    app.register_blueprint(auth_mod)
    app.register_blueprint(faction_mod)
    app.register_blueprint(bot_mod)
    app.register_blueprint(error_mod)
    app.register_blueprint(admin_mod)
    app.register_blueprint(stat_mod)
    app.register_blueprint(api_mod)
    app.register_blueprint(torn_mod)
    app.register_blueprint(skynet_mod)
