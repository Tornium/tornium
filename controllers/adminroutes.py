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

from functools import wraps

from flask import Blueprint, render_template, abort, request
from flask_login import login_required, current_user

from redisdb import get_redis
from models.factionmodel import FactionModel
from models.usermodel import UserModel
from tasks import faction as factiontasks
from tasks import guild as guildtasks
from tasks import stakeouts as stakeouttasks
from tasks import user as usertasks
import utils


mod = Blueprint('adminroutes', __name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.admin:
            return abort(403)
        else:
            return f(*args, **kwargs)

    return wrapper


@mod.route('/admin')
@login_required
@admin_required
def index():
    return render_template('admin/index.html')


@mod.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
@admin_required
def dashboard():
    if request.method == 'POST':
        if request.form.get('refreshfactions') is not None:
            factiontasks.refresh_factions.delay()
        elif request.form.get('refreshguilds') is not None:
            guildtasks.refresh_guilds.delay()
        elif request.form.get('refreshusers') is not None:
            usertasks.refresh_users.delay()
        elif request.form.get('fetchattacks') is not None:
            factiontasks.fetch_attacks.delay()
        elif request.form.get('refreshuserstakeouts') is not None:
            stakeouttasks.user_stakeouts.delay()
        elif request.form.get('refreshfactionstakeouts') is not None:
            stakeouttasks.faction_stakeouts.delay()

    return render_template('admin/dashboard.html')


@mod.route('/admin/bot', methods=['GET', 'POST'])
@login_required
@admin_required
def bot():
    redis = get_redis()

    if request.method == 'POST':
        if request.form.get('bottoken') is not None:
            redis.set('tornium:settings:bottoken', request.form.get('bottoken'))  # TODO: Replace bottoken in settings file

    return render_template('admin/bot.html', bottoken=redis.get('tornium:settings:bottoken'))


@mod.route('/admin/database')
@login_required
@admin_required
def database():
    return render_template('admin/database.html')


@mod.route('/admin/database/faction')
@login_required
@admin_required
def faction_database():
    return render_template('admin/factiondb.html')


@mod.route('/admin/database/faction/<int:tid>')
@login_required
@admin_required
def faction(tid: int):
    faction = utils.first(FactionModel.objects(tid=tid))

    return render_template('admin/faction.html', faction=faction)


@mod.route('/admin/database/factions')
@login_required
@admin_required
def factions():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    search_value = request.args.get('search[value]')

    factions = []

    if search_value is None:
        for faction in FactionModel.objects().all()[start:start+length]:
            factions.append([faction.tid, faction.name])
    else:
        for faction in FactionModel.objects(name__startswith=search_value)[start:start+length]:
            factions.append([faction.tid, faction.name])

    return {
        'draw': request.args.get('draw'),
        'recordsTotal': FactionModel.objects.count(),
        'recordsFiltered': FactionModel.objects.count(),
        'data': factions
    }


@mod.route('/admin/database/user')
@login_required
@admin_required
def user_database():
    return render_template('admin/userdb.html')


@mod.route('/admin/database/user/<int:tid>')
@login_required
@admin_required
def user(tid: int):
    user = utils.first(UserModel.objects(tid=tid))

    return render_template('admin/user.html', user=user)


@mod.route('/admin/database/users')
@login_required
@admin_required
def users():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    search_value = request.args.get('search[value]')

    users = []

    if search_value is None:
        for user in UserModel.objects().all()[start:start+length]:
            users.append([user.tid, user.name, user.discord_id if user.discord_id != 0 else ''])
    else:
        for user in UserModel.objects(name__startswith=search_value)[start:start+length]:
            users.append([user.tid, user.name, user.discord_id if user.discord_id != 0 else ''])

    return {
        'draw': request.args.get('draw'),
        'recordsTotal': UserModel.objects.count(),
        'recordsFiltered': UserModel.objects.count(),
        'data': users
    }
