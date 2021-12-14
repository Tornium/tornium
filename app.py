# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster.deeksh@gmail.com>

import logging

import flask
from flask_login import LoginManager
from mongoengine import connect

from controllers import mod as base_mod
from controllers.stat import mod as stat_mod
from controllers.api import mod as api_mod
from redisdb import get_redis
import utils

redis = get_redis()

connect(
    db='Tornium',
    username=redis.get('username'),
    password=redis.get('password'),
    host=f'mongodb://{redis.get("host")}',
    connect=False
)

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='server.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

app = flask.Flask(__name__)
app.secret_key = redis.get('secret')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'authroutes.login'
login_manager.refresh_view = 'authroutes.login'
login_manager.session_protection = 'basic'


@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return utils.first(User.objects(tid=user_id))


if redis.get("dev") == "True" and __name__ == "__main__":
    app.register_blueprint(base_mod)
    app.register_blueprint(stat_mod)
    app.register_blueprint(api_mod)

    app.run('localhost', 8080, debug=True)

if redis.get("dev") == "False":
    app.register_blueprint(base_mod)
    app.register_blueprint(stat_mod)
    app.register_blueprint(api_mod)
