# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template, request
from flask_login import login_required

from controllers.faction.decorators import *
from models.factionmodel import FactionModel
from models.user import User
from models.withdrawalmodel import WithdrawalModel
import utils


@login_required
@aa_required
def bankingaa():
    return render_template('faction/bankingaa.html')


@login_required
@aa_required
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
    faction: FactionModel = utils.first(FactionModel.objects(tid=current_user.factiontid))

    if faction is None:
        return render_template(
            'faction/banking.html',
            bankingenabled=False,
            key=current_user.key
        )

    return render_template(
        'faction/banking.html',
        bankingenabled=faction.vaultconfig['banking'] != 0 and faction.vaultconfig['banker'] != 0 and faction.vaultconfig['withdrawal'] != 0,
        key=current_user.key
    )


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
