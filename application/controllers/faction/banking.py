# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import typing

from flask import redirect, render_template, request
from flask_login import current_user, login_required
from peewee import JOIN, DataError, DoesNotExist
from tornium_celery.tasks.api import discordpatch
from tornium_celery.tasks.misc import send_dm
from tornium_commons.formatters import torn_timestamp
from tornium_commons.models import Faction, FactionPosition, Server, User, Withdrawal

import utils
from controllers.faction.decorators import aa_required, fac_required


@login_required
@fac_required
@aa_required
def banking_aa():
    return render_template("faction/banking_aa.html")


@login_required
@fac_required
@aa_required
def banking_data():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")
    withdrawals = []

    withdrawals_db = Withdrawal.select().where(Withdrawal.faction_tid == current_user.faction_id)

    if ordering == 0:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.wid))
    elif ordering == 1:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.amount))
    elif ordering == 2:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.requester))
    elif ordering == 4:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.fulfiller))
    elif ordering == 5:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.time_fulfilled))
    else:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.time_requested))

    withdrawals_db = withdrawals_db[start : start + length]

    withdrawal: Withdrawal
    for withdrawal in withdrawals_db:
        if withdrawal.status == 0:
            fulfiller_str = "Not Fulfilled"
        elif withdrawal.status == 1:
            fulfiller_str = User.user_str(withdrawal.fulfiller)
        elif withdrawal.status == 2:
            fulfiller_str = f"Cancelled by {User.user_str(withdrawal.fulfiller)}"
        elif withdrawal.status == 3:
            fulfiller_str = "Cancelled by System"
        else:
            fulfiller_str = "Unknown Status"

        time_fulfilled = (
            torn_timestamp(withdrawal.time_fulfilled.timestamp()) if withdrawal.time_fulfilled is not None else ""
        )

        withdrawals.append(
            [
                withdrawal.wid,
                (
                    f"${withdrawal.amount:,}" if withdrawal.cash_request else f"{withdrawal.amount:,} points"
                ),  # noqa: E712
                User.user_str(withdrawal.requester),
                torn_timestamp(withdrawal.time_requested),
                fulfiller_str,
                time_fulfilled,
            ]
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": Withdrawal.select().count(),
        "recordsFiltered": Withdrawal.select().where(Withdrawal.faction_tid == current_user.faction_id).count(),
        "data": withdrawals,
    }
    return data


@login_required
def banking():
    if current_user.faction is None:
        return render_template("faction/banking.html", banking_enabled=False)

    fifteen_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)

    banker_users = (
        User.select(User.tid, User.name, User.last_action, User.faction_position)
        .join(FactionPosition, JOIN.LEFT_OUTER)
        .order_by(User.last_action.desc())
        .where((User.tid.in_(current_user.faction.get_bankers())) & (User.last_action >= fifteen_minutes_ago))
    )
    bankers_data = [
        {
            "name": banker_user.name,
            "tid": banker_user.tid,
            "last_action": int(banker_user.last_action.timestamp()),
            "money": (
                "Money Giving" in banker_user.faction_position.permissions
                if banker_user.faction_position is not None
                else True
            ),
            "points": (
                "Points Giving" in banker_user.faction_position.permissions
                if banker_user.faction_position is not None
                else True
            ),
            "adjust": (
                "Balance Adjustment" in banker_user.faction_position.permissions
                if banker_user.faction_position is not None
                else True
            ),
        }
        for banker_user in banker_users
    ]

    try:
        guild: typing.Optional[Server] = current_user.faction.guild
    except DoesNotExist:
        guild = None

    if guild is None or str(current_user.faction_id) not in guild.banking_config:
        banking_enabled = False
    else:
        banking_enabled = guild.banking_config[str(current_user.faction_id)]["channel"]

    return render_template(
        "faction/banking.html",
        banking_enabled=banking_enabled,
        faction=current_user.faction,
        bankers=bankers_data,
    )


@login_required
def user_banking_data():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")
    withdrawals = []

    withdrawals_db = Withdrawal.select().where(Withdrawal.requester == current_user.tid)

    if ordering == 0:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.wid))
    elif ordering == 1:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.amount))
    elif ordering == 3:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.fulfiller))
    elif ordering == 4:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.time_fulfilled))
    else:
        withdrawals_db = withdrawals_db.order_by(utils.table_order(ordering_direction, Withdrawal.time_requested))

    withdrawals_db = withdrawals_db.paginate(start // length + 1, length)

    withdrawal: Withdrawal
    for withdrawal in withdrawals_db:
        if withdrawal.status == 0:
            fulfiller_str = "Not Fulfilled"
        elif withdrawal.status == 1:
            fulfiller_str = User.user_str(withdrawal.fulfiller)
        elif withdrawal.status == 2:
            fulfiller_str = f"Cancelled by {User.user_str(withdrawal.fulfiller)}"
        elif withdrawal.status == 3:
            fulfiller_str = "Cancelled by System"
        else:
            fulfiller_str = "Unknown Status"

        time_fulfilled = (
            torn_timestamp(withdrawal.time_fulfilled.timestamp()) if withdrawal.time_fulfilled is not None else ""
        )

        withdrawals.append(
            [
                withdrawal.wid,
                (f"${withdrawal.amount:,}" if withdrawal.cash_request else f"{withdrawal.amount:,} points"),
                torn_timestamp(withdrawal.time_requested),
                fulfiller_str,
                time_fulfilled,
            ]
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": Withdrawal.select().count(),
        "recordsFiltered": Withdrawal.select().where(Withdrawal.requester == current_user.tid).count(),
        "data": withdrawals,
    }
    return data


def fulfill(guid: str):
    fulfiller_id = current_user.tid if current_user.is_authenticated else -1
    fulfiller_string = current_user.user_str_self() if current_user.is_authenticated else "someone"

    try:
        original_withdrawal: Withdrawal = Withdrawal.select().where(Withdrawal.guid == guid).get()
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Withdrawal",
                error="The passed withdrawal could not be found in the database.",
            ),
            400,
        )
    except DataError:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Withdrawal Format",
                error="The passed withdrawal was invalidly formatted. Please make sure that you're not trying to fulfill a withdrawal from the far past as the format has changed.",
            ),
            400,
        )

    try:
        updated_withdrawal: Withdrawal = original_withdrawal.fulfill(
            fulfiller_id, fulfiller_string, discordpatch, send_dm
        )

        send_link = f"https://tcy.sh/s/{'bg' if updated_withdrawal.cash_request else 'pg'}?u={updated_withdrawal.requester}&a={updated_withdrawal.amount}"
        return redirect(send_link)
    except (DoesNotExist, IndexError):
        # If the updated withdrawal does not exist, some condition in the where clause failed.
        # We can just continue and expect a proper updated withdrawal to be handled inside of
        # the try clause
        pass

    if original_withdrawal.status == 1:
        return (
            render_template(
                "errors/error.html",
                title="Can't Fulfill Request",
                error=f"This request has already been fulfilled at {torn_timestamp(original_withdrawal.time_fulfilled.timestamp())}.",
            ),
            400,
        )
    elif original_withdrawal.status == 2:
        return (
            render_template(
                "errors/error.html",
                title="Can't Fulfill Request",
                error=f"This request has already been cancelled at {torn_timestamp(original_withdrawal.time_fulfilled.timestamp())}.",
            ),
            400,
        )
    elif original_withdrawal.status == 3:
        return (
            render_template(
                "errors/error.html",
                title="Can't Fulfill Request",
                error=f"This request has already been cancelled by the system at {torn_timestamp(original_withdrawal.time_fulfilled.timestamp())}.",
            ),
            400,
        )

    faction: Faction = original_withdrawal.faction
    if faction.guild is None:
        return (
            render_template(
                "errors/error.html",
                title="Missing Configuration",
                error="The server's vault configuration is not properly set. Please contact a server administrator or "
                "faction AA member to do so.",
            ),
            400,
        )
    elif faction.tid not in faction.guild.factions:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error="The faction is not set up to be in the specified server.",
            ),
            403,
        )
    elif faction.guild.banking_config.get(str(faction.tid), {"channel": "0"})["channel"] == "0":
        return (
            render_template(
                "errors/error.html",
                title="Missing Configuration",
                error="The server's vault configuration is not properly set. Please contact a server administrator or "
                "faction AA member to do so.",
            ),
            400,
        )

    return (
        render_template(
            "errors/error.html",
            title="Unable to Fulfill",
            error="For some unhandled reason, Tornium is unable to allow you to fulfill the vault request. "
            "Please create a ticket on the support Discord server.",
        ),
        500,
    )
