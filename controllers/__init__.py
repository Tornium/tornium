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

from flask import Blueprint, render_template, send_from_directory, request

mod = Blueprint('baseroutes', __name__)


@mod.route('/')
@mod.route('/index')
def index():
    return render_template('index.html')


@mod.route('/robots.txt')
@mod.route('/toast.js')
@mod.route('/favicon.svg')
@mod.route('/login.css')
@mod.route('/admin/database/faction.js')
@mod.route('/admin/database/user.js')
@mod.route('/bot/stakeouts.js')
@mod.route('/bot/guild.js')
@mod.route('/faction/banking.js')
@mod.route('/faction/bankingaa.js')
@mod.route('/faction/group.js')
@mod.route('/faction/schedule.js')
@mod.route('/faction/schedulechart.js')
@mod.route('/stats/db.js')
@mod.route('/stats/list.js')
def static():
    return send_from_directory('static', request.path[1:])
