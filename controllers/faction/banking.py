# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime

from flask import render_template, request, redirect
from flask_login import login_required

from controllers.faction.decorators import *
from models.factionmodel import FactionModel
from models.servermodel import ServerModel
from models.user import User
from models.withdrawalmodel import WithdrawalModel
import tasks
import utils
from utils.errors import DiscordError


@login_required
@aa_required
def bankingaa():
    return render_template("faction/bankingaa.html")


@login_required
@aa_required
def bankingdata():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    withdrawals = []

    for withdrawal in WithdrawalModel.objects(factiontid=current_user.factiontid)[
        start : start + length
    ]:
        requester = f"{User(withdrawal.requester).name} [{withdrawal.requester}]"
        fulfiller = (
            f"{User(withdrawal.fulfiller).name} [{withdrawal.fulfiller}]"
            if withdrawal.fulfiller != 0
            else ""
        )
        timefulfilled = (
            utils.torn_timestamp(withdrawal.time_fulfilled)
            if withdrawal.time_fulfilled != 0
            else ""
        )

        withdrawals.append(
            [
                withdrawal.wid,
                f"${withdrawal.amount:,}",
                requester,
                utils.torn_timestamp(withdrawal.time_requested),
                fulfiller,
                timefulfilled,
            ]
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": WithdrawalModel.objects().count(),
        "recordsFiltered": WithdrawalModel.objects(
            factiontid=current_user.factiontid
        ).count(),
        "data": withdrawals,
    }
    return data


@login_required
def banking():
    faction: FactionModel = FactionModel.objects(tid=current_user.factiontid).first()

    if faction is None:
        return render_template(
            "faction/banking.html", bankingenabled=False, key=current_user.key
        )

    return render_template(
        "faction/banking.html",
        bankingenabled=faction.vaultconfig["banking"] != 0
        and faction.vaultconfig["banker"] != 0
        and faction.vaultconfig["withdrawal"] != 0,
        key=current_user.key,
        faction=faction,
    )


@login_required
def userbankingdata():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    withdrawals = []

    for withdrawal in WithdrawalModel.objects(requester=current_user.tid)[
        start : start + length
    ]:
        fulfiller = (
            f"{User(withdrawal.fulfiller).name} [{withdrawal.fulfiller}]"
            if withdrawal.fulfiller != 0
            else ""
        )
        timefulfilled = (
            utils.torn_timestamp(withdrawal.time_fulfilled)
            if withdrawal.time_fulfilled != 0
            else ""
        )

        withdrawals.append(
            [
                withdrawal.wid,
                f"${withdrawal.amount:,}",
                utils.torn_timestamp(withdrawal.time_requested),
                fulfiller,
                timefulfilled,
            ]
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": WithdrawalModel.objects().count(),
        "recordsFiltered": WithdrawalModel.objects(requester=current_user.tid).count(),
        "data": withdrawals,
    }
    return data


@login_required
def fulfill(wid: int):
    withdrawal: WithdrawalModel = WithdrawalModel.objects(wid=wid).first()
    if withdrawal.wtype in [0, None]:
        send_link = f"https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user&giveMoneyTo={withdrawal.requester}&money={withdrawal.amount}"
    else:
        send_link = f"https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user&givePointsTo={withdrawal.requester}&points={withdrawal.amount}"

    if withdrawal is None:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Withdrawal",
                error="The passed withdrawal could not be found in the database.",
            ),
            400,
        )
    elif withdrawal.fulfiller != 0:
        return redirect(send_link)
    elif current_user.factiontid != withdrawal.factiontid:
        return (
            render_template(
                "errors/error.html",
                title="Faction Mismatch",
                error="The faction of the fulfilling user does not match the originating faction of the request",
            ),
            400,
        )

    faction: FactionModel = FactionModel.objects(tid=current_user.factiontid).first()

    if faction is None:
        return (
            render_template(
                "errors/error.html",
                title="Faction Not Found",
                error="The fulfilling user's faction could not be located in the database.",
            ),
            400,
        )
    elif (
        faction.vaultconfig.get("banking") in [0, None]
        or faction.vaultconfig.get("banker") in [0, None]
        or faction.config.get("vault") in [0, None]
        or faction.guild == 0
    ):
        return (
            render_template(
                "errors/error.html",
                title="Missing Configuration",
                error="The server's vault configuration is not properly set. Please contact a server administrator or faction AA member to do so.",
            ),
            400,
        )

    guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

    if guild is None:
        return render_template(
            "errors/error.html",
            title="Unknown Server",
            error="The faction's Discord server could not be located in the database.",
        )

    channels = tasks.discordget(f"guilds/{faction.guild}/channels")
    banking_channel = None

    for channel in channels:
        if channel["id"] == str(faction.vaultconfig.get("banking")):
            banking_channel = channel
            break

    if banking_channel is None:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Channel",
                error="The banking channnel withdrawal requests are sent to could not be found.",
            ),
            400,
        )

    try:
        message = tasks.discordpatch(
            f"channels/{banking_channel['id']}/messages/{withdrawal.withdrawal_message}",
            payload={
                "embeds": [
                    {
                        "title": f"Vault Request #{withdrawal.wid}",
                        "description": f"This request has been fulfilled by {current_user.name} [{current_user.tid}].",
                        "fields": [
                            {
                                "name": "Original Request Amount",
                                "value": utils.commas(withdrawal.amount),
                            },
                            {
                                "name": "Original Request Type",
                                "value": "Points" if withdrawal.wtype == 1 else "Cash",
                            },
                        ],
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                    }
                ],
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Faction Vault",
                                "url": "https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user",
                            },
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Fulfill",
                                "url": f"https://tornium.com/faction/banking/fulfill/{withdrawal.wid}",
                            },
                            {
                                "type": 2,
                                "style": 3,
                                "label": "Fulfill Manually",
                                "custom_id": "faction:vault:fulfill",
                            },
                        ],
                    }
                ],
            },
        )
    except DiscordError as e:
        return utils.handle_discord_error(e)

    withdrawal.fulfiller = current_user.tid
    withdrawal.time_fulfilled = utils.now()
    withdrawal.save()

    return redirect(send_link)
