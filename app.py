# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import logging

import flask
from flask_cors import CORS
from flask_login import LoginManager
import honeybadger
from honeybadger.contrib import FlaskHoneybadger
from mongoengine import connect

import settings  # Do not remove - initializes redis values
from redisdb import get_redis


redis = get_redis()
honeybadger.honeybadger.configure(api_key=redis.get('tornium:settings:honeykey'))

connect(
    db='Tornium',
    username=redis.get('tornium:settings:username'),
    password=redis.get('tornium:settings:password'),
    host=f'mongodb://{redis.get("tornium:settings:host")}',
    connect=False
)

from controllers import mod as base_mod
from controllers.authroutes import mod as auth_mod
from controllers.faction import mod as faction_mod
from controllers.bot import mod as bot_mod
from controllers.errors import mod as error_mod
from controllers.adminroutes import mod as admin_mod
from controllers.statroutes import mod as stat_mod
from controllers.api import mod as api_mod
import utils

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='server.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

app = flask.Flask(__name__)
app.secret_key = redis.get('tornium:settings:secret')
app.config['HONEYBADGER_ENVIRONMENT'] = redis.get('tornium:settings:honeyenv')
app.config['HONEYBADGER_API_KEY'] = redis.get('tornium:settings:honeykey')
app.config['HONEYBADGER_PARAMS_FILTERS'] = 'password, secret, credit-card'
app.config['REMEMBER_COOKIE_DURATION'] = 604800
FlaskHoneybadger(app, report_exceptions=True)

cors = CORS(app, resources={r'/api/*': {'origins': '*'}})

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'authroutes.login'
login_manager.refresh_view = 'authroutes.login'
login_manager.session_protection = 'strong'


@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User(user_id)


@app.template_filter('reltime')
def relative_time(s):
    return utils.rel_time(datetime.datetime.fromtimestamp(s))


@app.template_filter('tcttime')
def tct_time(s):
    return utils.torn_timestamp(int(s))


if redis.get('tornium:settings:dev') == 'True' and __name__ == "__main__":
    app.register_blueprint(base_mod)
    app.register_blueprint(auth_mod)
    app.register_blueprint(faction_mod)
    app.register_blueprint(bot_mod)
    app.register_blueprint(error_mod)
    app.register_blueprint(admin_mod)
    app.register_blueprint(stat_mod)
    app.register_blueprint(api_mod)

    app.run('localhost', 8000, debug=True)

if redis.get('tornium:settings:dev') == 'False':
    app.register_blueprint(base_mod)
    app.register_blueprint(auth_mod)
    app.register_blueprint(faction_mod)
    app.register_blueprint(bot_mod)
    app.register_blueprint(error_mod)
    app.register_blueprint(admin_mod)
    app.register_blueprint(stat_mod)
    app.register_blueprint(api_mod)
