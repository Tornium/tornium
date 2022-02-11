# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

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
@mod.route('/faction/recruitment.js')
@mod.route('/faction/schedule.js')
@mod.route('/faction/schedulechart.js')
@mod.route('/stats/db.js')
@mod.route('/stats/list.js')
def static():
    return send_from_directory('static', request.path[1:])
