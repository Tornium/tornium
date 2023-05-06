# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import time
import typing

from flask import redirect, render_template, request
from flask_login import current_user, login_required
from mongoengine.queryset.visitor import Q
from tornium_celery.tasks.api import discordget, discordpatch, discordpost
from tornium_commons.errors import DiscordError
from tornium_commons.formatters import commas, torn_timestamp
from tornium_commons.models import (
    FactionModel,
    PositionModel,
    ServerModel,
    UserModel,
    WithdrawalModel,
)
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

import utils
from controllers.faction.decorators import aa_required
from models.user import User


@login_required
@aa_required
def bankingaa():
    return render_template("faction/bankingaa.html")


@login_required
@aa_required
def bankingdata():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")
    withdrawals = []

    if ordering_direction == "asc":
        ordering_direction = "+"
    else:
        ordering_direction = "-"

    withdrawals_db = WithdrawalModel.objects(factiontid=current_user.factiontid)

    if ordering == 0:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}wid")
    elif ordering == 1:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}amount")
    elif ordering == 2:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}requester")
    elif ordering == 4:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}fulfiller")
    elif ordering == 5:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}time_fulfilled")
    else:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}time_requested")

    withdrawals_db = withdrawals_db[start : start + length]

    for withdrawal in withdrawals_db:
        requester = f"{User(withdrawal.requester).name} [{withdrawal.requester}]"

        if withdrawal.fulfiller > 0:
            fulfiller = f"{User(withdrawal.fulfiller).name} [{withdrawal.fulfiller}]"
        elif withdrawal.fulfiller == -1:
            fulfiller = "Cancelled by System"
        elif withdrawal.fulfiller < -1:
            fulfiller = f"Cancelled by {User(-withdrawal.fulfiller).name} [{-withdrawal.fulfiller}]"
        else:
            fulfiller = ""

        timefulfilled = torn_timestamp(withdrawal.time_fulfilled) if withdrawal.time_fulfilled != 0 else ""

        withdrawals.append(
            [
                withdrawal.wid,
                f"${withdrawal.amount:,}" if withdrawal.wtype == 0 else f"{withdrawal.amount:,} points",
                requester,
                torn_timestamp(withdrawal.time_requested),
                fulfiller,
                timefulfilled,
            ]
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": WithdrawalModel.objects().count(),
        "recordsFiltered": WithdrawalModel.objects(factiontid=current_user.factiontid).count(),
        "data": withdrawals,
    }
    return data


@login_required
def banking():
    faction: FactionModel = FactionModel.objects(tid=current_user.factiontid).first()

    if faction is None:
        return render_template("faction/banking.html", bankingenabled=False, key=current_user.key)

    banker_positions = PositionModel.objects(
        Q(factiontid=faction.tid) & (Q(canGiveMoney=True) | Q(canGivePoints=True) | Q(canAdjustMemberBalance=True))
    )
    bankers = []

    banker_position: PositionModel
    for banker_position in banker_positions:
        users = UserModel.objects(faction_position=banker_position.pid)

        user: UserModel
        for user in users:
            bankers.append(
                {
                    "name": user.name,
                    "tid": user.tid,
                    "last_action": user.last_action,
                    "position": banker_position.name,
                    "money": banker_position.canGiveMoney,
                    "points": banker_position.canGivePoints,
                    "adjust": banker_position.canAdjustMemberBalance,
                }
            )

    if faction.leader != 0:
        user: UserModel = UserModel.objects(tid=faction.leader).first()

        if user is not None:
            bankers.append(
                {
                    "name": user.name,
                    "tid": user.tid,
                    "last_action": user.last_action,
                    "position": "Leader",
                    "money": True,
                    "points": True,
                    "adjust": True,
                }
            )

    if faction.coleader != 0:
        user: UserModel = UserModel.objects(tid=faction.coleader).first()

        if user is not None:
            bankers.append(
                {
                    "name": user.name,
                    "tid": user.tid,
                    "last_action": user.last_action,
                    "position": "Co-leader",
                    "money": True,
                    "points": True,
                    "adjust": True,
                }
            )

    guild: typing.Optional[ServerModel] = ServerModel.objects(sid=faction.guild).first() if faction.guild != 0 else None

    if guild is None or str(faction.tid) not in guild.banking_config:
        banking_enabled = False
    else:
        banking_enabled = guild.banking_config[str(faction.tid)]["channel"]

    return render_template(
        "faction/banking.html",
        bankingenabled=banking_enabled,
        key=current_user.key,
        faction=faction,
        bankers=bankers,
    )


@login_required
def userbankingdata():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")
    withdrawals = []

    if ordering_direction == "asc":
        ordering_direction = "+"
    else:
        ordering_direction = "-"

    withdrawals_db = WithdrawalModel.objects(requester=current_user.tid)

    if ordering == 0:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}wid")
    elif ordering == 1:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}amount")
    elif ordering == 3:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}fulfiller")
    elif ordering == 4:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}time_fulfilled")
    else:
        withdrawals_db = withdrawals_db.order_by(f"{ordering_direction}time_requested")

    withdrawals_db = withdrawals_db[start : start + length]

    for withdrawal in withdrawals_db:
        if withdrawal.fulfiller > 0:
            fulfiller = f"{User(withdrawal.fulfiller).name} [{withdrawal.fulfiller}]"
        elif withdrawal.fulfiller == -1:
            fulfiller = "Cancelled by System"
        elif withdrawal.fulfiller < -1:
            fulfiller = f"Cancelled by {User(-withdrawal.fulfiller).name} [{-withdrawal.fulfiller}]"
        else:
            fulfiller = ""

        timefulfilled = torn_timestamp(withdrawal.time_fulfilled) if withdrawal.time_fulfilled != 0 else ""

        withdrawals.append(
            [
                withdrawal.wid,
                f"${withdrawal.amount:,}" if withdrawal.wtype == 0 else f"{withdrawal.amount:,} points",
                torn_timestamp(withdrawal.time_requested),
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


def fulfill(uuid: str):
    withdrawal: WithdrawalModel = WithdrawalModel.objects(uuid=uuid).first()

    if withdrawal.wtype in [0, None]:
        send_link = (
            f"https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user&giveMoneyTo="
            f"{withdrawal.requester}&money={withdrawal.amount}"
        )
    else:
        send_link = (
            f"https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user&givePointsTo="
            f"{withdrawal.requester}&points={withdrawal.amount}"
        )

    if withdrawal is None:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Withdrawal",
                error="The passed withdrawal could not be found in the database. If this request is older than May 6th, the request is no longer supported after backend schema update.",
            ),
            400,
        )
    elif withdrawal.fulfiller != 0:  # Already fulfilled or cancelled
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
    elif faction.guild == 0:
        return (
            render_template(
                "errors/error.html",
                title="Missing Configuration",
                error="The server's vault configuration is not properly set. Please contact a server administrator or "
                "faction AA member to do so.",
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
    elif faction.tid not in guild.factions:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error="The faction is not set up to be in the specified server.",
            ),
            403,
        )
    elif guild.banking_config.get(str(faction.tid), {"channel": "0"})["channel"] == "0":
        return (
            render_template(
                "errors/error.html",
                title="Missing Configuration",
                error="The server's vault configuration is not properly set. Please contact a server administrator or "
                "faction AA member to do so.",
            ),
            400,
        )

    channels = discordget(f"guilds/{faction.guild}/channels")
    banking_channel = None

    for channel in channels:
        if channel["id"] == guild.banking_config[str(faction.tid)]["channel"]:
            banking_channel = channel
            break

    if banking_channel is None:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Channel",
                error="The banking channel withdrawal requests are sent to could not be found.",
            ),
            400,
        )

    requester: typing.Optional[UserModel] = UserModel.objects(tid=withdrawal.requester).first()

    try:
        discordpatch(
            f"channels/{banking_channel['id']}/messages/{withdrawal.withdrawal_message}",
            payload={
                "embeds": [
                    {
                        "title": f"Vault Request #{withdrawal.wid}",
                        "description": f"This request has been fulfilled by {current_user.name} [{current_user.tid}].",
                        "fields": [
                            {
                                "name": "Original Request Amount",
                                "value": commas(withdrawal.amount),
                            },
                            {
                                "name": "Original Request Type",
                                "value": "Points" if withdrawal.wtype == 1 else "Cash",
                            },
                            {
                                "name": "Original Requester",
                                "value": f"{'Unknown' if requester is None else requester.name} [{withdrawal.requester}]",
                            },
                        ],
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "color": SKYNET_GOOD,
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
                                "url": f"https://tornium.com/faction/banking/fulfill/{withdrawal.guid}",
                            },
                            {
                                "type": 2,
                                "style": 3,
                                "label": "Fulfill Manually",
                                "custom_id": "faction:vault:fulfill",
                            },
                            {
                                "type": 2,
                                "style": 4,
                                "label": "Cancel",
                                "custom_id": "faction:vault:cancel",
                            },
                        ],
                    }
                ],
            },
        )
    except DiscordError as e:
        return utils.handle_discord_error(e)

    if current_user.is_authenticated:
        withdrawal.fulfiller = current_user.tid
    else:
        withdrawal.fulfiller = 1

    withdrawal.time_fulfilled = int(time.time())
    withdrawal.save()

    if requester.discord_id not in (None, "", 0):
        try:
            dm_channel = discordpost("users/@me/channels", payload={"recipient_id": requester.discord_id})
        except Exception:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Banking Request {withdrawal.wid} Fulfilled",
                            "description": "You have fulfilled the banking request.",
                            "color": SKYNET_GOOD,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        discordpost.delay(
            f"channels/{dm_channel['id']}/messages",
            payload={
                "embeds": [
                    {
                        "title": "Vault Request Fulfilled",
                        "description": f"Your vault request #{withdrawal.wid} has been fulfilled by someone.",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        ).forget()

    return redirect(send_link)
