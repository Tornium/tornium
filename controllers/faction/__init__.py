# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

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
