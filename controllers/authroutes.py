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

from flask import Blueprint, request, redirect, render_template, abort, url_for
from flask_login import logout_user, login_user
from is_safe_url import is_safe_url

from models.user import User
from redisdb import get_redis
import tasks
import utils


mod = Blueprint('authroutes', __name__)


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    global torn_user

    try:
        key_info = tasks.tornget(endpoint='key/?selections=info', key=request.form['key'])
    except utils.TornError as e:
        return utils.handle_torn_error(str(e))
    except Exception as e:
        return render_template('errors/error.html', title='Error', message=str(e))

    if key_info['access_level'] < 3:
        return render_template('errors/error.html', title='Bad API Key',
                               message='Only Torn API keys that are full or limited access can currently be used. '
                                       'Keys with custom permissions are not currently supported either.')

    try:
        torn_user = tasks.tornget(endpoint='user/?selections=', key=request.form['key'])
    except utils.TornError as e:
        return utils.handle_torn_error(str(e))
    except Exception as e:
        return render_template('errors/error.html', title='Error', message=str(e))

    user = User(torn_user['player_id'])

    if user.key != request.form['key']:
        user.set_key(request.form['key'])

    user.refresh()
    user.faction_refresh()
    login_user(user)
    next = request.args.get('next')

    if next is None or next == 'None':
        return redirect(url_for('baseroutes.index'))

    if not get_redis().get('tornium:settings:dev'):
        if not is_safe_url(next, {'torn.deek.sh'}):
            abort(400)
    return redirect(next or url_for('baseroutes.index'))


@mod.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('baseroutes.index'))

