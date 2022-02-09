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

from flask import Blueprint, render_template

from controllers.api import key
from controllers.api import stakeout
from controllers.api import stat
from controllers.api import user
from controllers.api.faction import banking, group, schedule

mod = Blueprint('apiroutes', __name__)


# /api/key
mod.add_url_rule('/api/key', view_func=key.test_key, methods=['GET'])
mod.add_url_rule('/api/key', view_func=key.create_key, methods=['POST'])
mod.add_url_rule('/api/key', view_func=key.remove_key, methods=['DELETE'])

# /api/faction
mod.add_url_rule('/api/faction/banking', view_func=banking.banking_request, methods=['POST'])
mod.add_url_rule('/api/faction/group', view_func=group.group_modify, methods=['POST'])
mod.add_url_rule('/api/faction/schedule', view_func=schedule.create_schedule, methods=['POST'])
mod.add_url_rule('/api/faction/schedule', view_func=schedule.delete_schedule, methods=['DELETE'])
mod.add_url_rule('/api/faction/schedule/setup', view_func=schedule.schedule_setup, methods=['POST'])
mod.add_url_rule('/api/faction/schedule/watcher/<string:uuid>', view_func=schedule.get_schedule, methods=['GET'])
mod.add_url_rule('/api/faction/schedule/watcher', view_func=schedule.add_chain_watcher, methods=['POST'])
mod.add_url_rule('/api/faction/schedule/watcher', view_func=schedule.remove_chain_watcher, methods=['DELETE'])
mod.add_url_rule('/api/faction/schedule/activity', view_func=schedule.add_chain_availability, methods=['POST'])

# /api/stakeout
mod.add_url_rule('/api/stakeout/<string:stype>', view_func=stakeout.create_stakeout, methods=['POST'])

# /api/stat
mod.add_url_rule('/api/stat', view_func=stat.generate_chain_list, methods=['GET'])
mod.add_url_rule('/api/stat/<int:tid>', view_func=stat.get_stat_user, methods=['GET'])

# /api/user
mod.add_url_rule('/api/user', view_func=user.get_user, methods=['GET'])


@mod.route('/api')
def index():
    return render_template('api/index.html')
