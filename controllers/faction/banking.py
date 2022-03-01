# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template, request
from flask_login import login_required

from controllers.faction.decorators import *
from models.user import User
from models.withdrawalmodel import WithdrawalModel
import utils


@aa_required
@login_required
def bankingaa():
    return render_template('faction/bankingaa.html')


@aa_required
@login_required
def bankingdata():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    withdrawals = []

    for withdrawal in WithdrawalModel.objects(factiontid=current_user.factiontid)[start:start+length]:
        requester = f'{User(withdrawal.requester).name} [{withdrawal.requester}]'
        fulfiller = f'{User(withdrawal.fulfiller).name} [{withdrawal.fulfiller}]' if withdrawal.fulfiller != 0 else ''
        timefulfilled = utils.torn_timestamp(withdrawal.time_fulfilled) if withdrawal.time_fulfilled != 0 else ''

        withdrawals.append([withdrawal.wid, f'${withdrawal.amount:,}', requester,
                            utils.torn_timestamp(withdrawal.time_requested), fulfiller, timefulfilled])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': WithdrawalModel.objects().count(),
        'recordsFiltered': WithdrawalModel.objects(factiontid=current_user.factiontid).count(),
        'data': withdrawals
    }
    return data


@login_required
def banking():
    return render_template('faction/banking.html', key=current_user.key)


@login_required
def userbankingdata():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    withdrawals = []

    for withdrawal in WithdrawalModel.objects(requester=current_user.tid)[start:start+length]:
        fulfiller = f'{User(withdrawal.fulfiller).name} [{withdrawal.fulfiller}]' if withdrawal.fulfiller != 0 else ''
        timefulfilled = utils.torn_timestamp(withdrawal.time_fulfilled) if withdrawal.time_fulfilled != 0 else ''

        withdrawals.append([withdrawal.wid, f'${withdrawal.amount:,}', utils.torn_timestamp(withdrawal.time_requested),
                            fulfiller, timefulfilled])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': WithdrawalModel.objects().count(),
        'recordsFiltered': WithdrawalModel.objects(requester=current_user.tid).count(),
        'data': withdrawals
    }
    return data
