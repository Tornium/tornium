# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from flask import render_template, request
from flask_login import login_required, current_user

from controllers.faction.decorators import fac_required
from models.factionmodel import FactionModel
from tasks import tornget


@login_required
@fac_required
def armory(*args, **kwargs):
    return render_template('faction/armory.html')


@login_required
@fac_required
def armoryitemdata(*args, **kwargs):
    if current_user.aa:
        key = current_user.key
    else:
        faction: FactionModel = kwargs['faction']

        if faction is None:
            return {}
        elif len(faction.keys) == 0:
            return {}

        key = random.choice(faction.keys)

    armorydata = tornget('faction/?selections=armor,temporary,weapons', key=key)
    data = []

    for armor in armorydata['armor']:
        data.append([
            f'{armor["name"]} [{armor["ID"]}]',
            armor['quantity'],
            armor['available'],
            armor['loaned']
        ])

    for temporary in armorydata['temporary']:
        data.append([
            f'{temporary["name"]} [{temporary["ID"]}]',
            temporary['quantity'],
            temporary['available'],
            temporary['loaned']
        ])

    for weapon in armorydata['weapons']:
        data.append([
            f'{weapon["name"]} [{weapon["ID"]}]',
            weapon['quantity'],
            weapon['available'],
            weapon['loaned']
        ])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': len(data),
        'data': data
    }
    return data
