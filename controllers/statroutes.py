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
import json
import math

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q

import utils
from controllers.faction.decorators import aa_required
from models.faction import Faction
from models.factiongroupmodel import FactionGroupModel
from models.factionmodel import FactionModel
from models.statmodel import StatModel
from models.user import User
from models.usermodel import UserModel

mod = Blueprint('statroutes', __name__)


@mod.route('/stats')
def index():
    return render_template('stats/index.html')


@mod.route('/stats/db')
@login_required
def stats():
    return render_template('stats/db.html', battlescore=current_user.battlescore)


@mod.route('/stats/dbdata')
@login_required
def stats_data():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    search_value = request.args.get('search[value]')

    stats = []

    if utils.get_tid(search_value):
        stat_entries = StatModel.objects(Q(tid__startswith=utils.get_tid(search_value)) & (Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid)))
    else:
        stat_entries = StatModel.objects(Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid))

    count = stat_entries.count()
    stat_entries = stat_entries[start:start+length]

    for stat_entry in stat_entries:
        stats.append([stat_entry.tid, int(stat_entry.battlescore),
                      utils.rel_time(datetime.datetime.fromtimestamp(stat_entry.timeadded))])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': StatModel.objects().count(),
        'recordsFiltered': count,
        'data': stats
    }

    return data


@mod.route('/stats/userdata')
@login_required
def user_data():
    tid = int(request.args.get('user'))
    stats = []
    stat_entries = StatModel.objects(Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid))

    factions = {}
    users = {}

    for stat_entry in stat_entries:
        if stat_entry.tid != tid:
            continue

        if str(stat_entry.addedid) in users:
            user = users[str(stat_entry.addedid)]
        else:
            user = utils.first(UserModel.objects(tid=stat_entry.addedid))
            users[str(stat_entry.addedid)] = user

        if str(stat_entry.addedfactiontid) in factions:
            faction = factions[str(stat_entry.addedfactiontid)]
        else:
            faction = utils.first(FactionModel.objects(tid=stat_entry.addedfactiontid))
            factions[str(stat_entry.addedfactiontid)] = faction

        stats.append({
            'statid': stat_entry.statid,
            'tid': stat_entry.tid,
            'battlescore': stat_entry.battlescore,
            'timeadded': stat_entry.timeadded,
            'addedid': user,
            'addedfactiontid': faction,
            'globalstat': stat_entry.globalstat
        })

    user = User(tid=tid)
    
    # If user's last action was over a month ago and last refresh was over a week ago
    if utils.now() - user.last_action > 30 * 24 * 60 * 60 and utils.now() - user.last_refresh > 604800:
        user.refresh(key=current_user.key)
    elif utils.now() - user.last_action <= 30 * 24 * 60 * 60:
        user.refresh(key=current_user.key)

    if user.factiontid != 0:
        faction = Faction(tid=user.factiontid)
    else:
        faction = None

    ff = 1 + (8 / 3 * stats[-1]['battlescore'] / current_user.battlescore)
    ff = ff if ff <= 3 else 3
    respect = math.log(user.level + 1) / 4 * ff

    return render_template('stats/statmodal.html', user=user, faction=faction, stats=stats, ff=round(ff, 2),
                           respect=round(respect, 2))


@mod.route('/stats/chain')
@login_required
def chain():
    return render_template('stats/chain.html', key=current_user.key)


@mod.route('/stats/config', methods=['GET', 'POST'])
@login_required
@aa_required
def config():
    faction = Faction(current_user.factiontid)

    if request.method == 'POST':
        faction_model = utils.first(FactionModel.objects(tid=current_user.factiontid))

        if (request.form.get('enabled') is not None) ^ (request.form.get('disabled') is not None):
            config = faction.stat_config

            if request.form.get('enabled') is not None:
                config['global'] = 1
                faction_model.statconfig = json.dumps(config)
            else:
                config['global'] = 0
                faction_model.statconfig = json.dumps(config)

            faction_model.save()

    return render_template('stats/config.html', config=faction.stat_config)
