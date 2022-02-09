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
from flask_login import login_required, current_user

from controllers.faction import banking, bot, chain, groups, schedule
from models.usermodel import UserModel

mod = Blueprint('factionroutes', __name__)

# Banking Routes
mod.add_url_rule('/faction/bankingaa', view_func=banking.bankingaa, methods=['GET'])
mod.add_url_rule('/faction/bankingdata', view_func=banking.bankingdata, methods=['GET'])
mod.add_url_rule('/faction/banking', view_func=banking.banking, methods=['GET'])
mod.add_url_rule('/faction/userbankingdata', view_func=banking.userbankingdata, methods=['GET'])

# Bot Routes
mod.add_url_rule('/faction/bot', view_func=bot.bot, methods=['GET', 'POST'])

# Chain Routes
mod.add_url_rule('/faction/chain', view_func=chain.chain, methods=['GET', 'POST'])

# Group Routes
mod.add_url_rule('/faction/groups', view_func=groups.groups, methods=['GET'])
mod.add_url_rule('/faction/groups/create', view_func=groups.create_group, methods=['GET'])
mod.add_url_rule('/faction/group/<int:tid>', view_func=groups.group, methods=['GET'])
mod.add_url_rule('/faction/group/invite/<string:invite>', view_func=groups.group_invite, methods=['GET'])

# Schedule Routes
mod.add_url_rule('/faction/schedule', view_func=schedule.schedule, methods=['GET'])
mod.add_url_rule('/faction/scheduledata', view_func=schedule.schedule, methods=['GET'])


@mod.route('/faction')
def index():
    return render_template('faction/index.html')
