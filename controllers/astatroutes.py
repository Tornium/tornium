# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime

from flask import Blueprint, request
from flask_login import login_required
from mongoengine.queryset.visitor import Q

from controllers.decorators import *
from models.astatmodel import AStatModel
from models.faction import Faction
from models.factionmodel import FactionModel
from models.user import User
from models.usermodel import UserModel
import utils

mod = Blueprint('astatroutes', __name__)


@mod.route('/astats')
@login_required
@pro_required
def index():
    return render_template('astats/index.html')


@mod.route('/astats/db')
@login_required
@pro_required
def stats():
    return render_template('astats/db.html')


@mod.route('/astats/dbdata')
@login_required
@pro_required
def stats_data():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    search_value = request.args.get('search[value]')

    stats = []

    if utils.get_tid(search_value):
        stat_entries = AStatModel.objects(Q(tid__startswith=utils.get_tid(search_value)) & (Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid)))
    else:
        stat_entries = AStatModel.objects(Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid))

    count = stat_entries.count()
    stat_entries = stat_entries[start:start+length]

    stat_entry: AStatModel
    for stat_entry in stat_entries:
        stats.append([
            stat_entry.tid,
            'N/I',
            utils.rel_time(datetime.datetime.fromtimestamp(stat_entry.timeadded))
        ])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': AStatModel.objects().count(),
        'recordsFiltered': count,
        'data': stats
    }

    return data


@mod.route('/astats/userdata')
@login_required
@pro_required
def user_data():
    tid = int(request.args.get('user'))
    stats = []
    stat_entries = AStatModel.objects(Q(tid=tid) & (Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid)))

    factions = {}
    users = {}

    stat_entry: AStatModel
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
            'statid': stat_entry.sid,
            'tid': stat_entry.tid,
            'timeadded': stat_entry.timeadded,
            'addedid': stat_entry.addedid,
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



    respect = 0
    ff = 0

    return render_template('stats/statmodal.html', user=user, faction=faction, stats=stats, ff=round(ff, 2),
                           respect=round(respect, 2))

