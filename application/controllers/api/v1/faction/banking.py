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
import json
import random
import uuid

from flask import jsonify, request
from peewee import DataError, DoesNotExist
from tornium_celery.tasks.api import discorddelete, discordpatch, discordpost, tornget
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.formatters import text_to_num
from tornium_commons.models import User, Withdrawal

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth(["faction:banking", "faction"])
@ratelimit
def vault_balance(*args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]

    if user.faction is None:
        return make_exception_response("1102", key)
    elif len(user.faction.aa_keys) == 0:
        return make_exception_response("1201", key)

    try:
        vault_balances = tornget("faction/?selections=donations", random.choice(user.faction.aa_keys))
    except TornError as e:
        return make_exception_response(
            "4100",
            key,
            details={
                "code": e.code,
                "error": e.error,
                "message": e.message,
            },
        )
    except NetworkingError as e:
        return make_exception_response(
            "4101",
            key,
            details={
                "code": e.code,
                "message": e.message,
            },
        )

    if str(user.tid) in vault_balances["donations"]:
        return (
            jsonify(
                {
                    "player_id": user.tid,
                    "faction_id": user.faction_id,
                    "money_balance": vault_balances["donations"][str(user.tid)]["money_balance"],
                    "points_balance": vault_balances["donations"][str(user.tid)]["points_balance"],
                }
            ),
            200,
            api_ratelimit_response(key),
        )
    else:
        return make_exception_response("1100", key)


@require_oauth(["faction:banking", "faction"])
@ratelimit
def new_banking_request(faction_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]

    amount = data.get("amount")
    withdrawal_option = data.get("type")
    timeout = data.get("timeout")

    if withdrawal_option is None or withdrawal_option not in ("points_balance", "money_balance"):
        return make_exception_response(
            "1000", key, details={"message": "The request `type` must be either `money_balance` or `points_balance`."}
        )

    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    timeout_datetime = None

    if isinstance(timeout, int):
        timeout_datetime = datetime.datetime.fromtimestamp(timeout, tz=datetime.timezone.utc)
    if timeout is not None and timeout_datetime <= now:
        return make_exception_response(
            "1000", key, details={"message": "The provided timeout value must be greater than the current timestamp."}
        )

    if amount is None:
        return make_exception_response("1000", key, details={"message": "The `amount` parameter is required."})
    elif amount.lower() == "all":
        parsed_amount = "all"
    elif isinstance(amount, int):
        parsed_amount = int(amount)
    elif isinstance(amount, str) and amount.isnumeric():
        parsed_amount = int(amount)
    elif isinstance(amount, str):
        try:
            parsed_amount = text_to_num(amount)
        except ValueError:
            return make_exception_response("1000", key, details={"message": "The provided amount is not valid."})
    else:
        return make_exception_response("1000", key, details={"message": "The provided amount is not valid."})

    try:
        validated_withdrawal_amount = Withdrawal.has_sufficient_balance(
            user.tid, user.faction_id, parsed_amount, withdrawal_option
        )
    except ValueError as e:
        return make_exception_response("1000", key, details={"message": str(e)})

    if user is None:
        return make_exception_response("1100", key)
    elif user.faction is None:
        return make_exception_response("1102", key)
    elif user.faction_id != faction_id:
        return make_exception_response("4022", key)
    elif user.faction.guild is None:
        return make_exception_response("1001", key)
    elif len(user.faction.aa_keys) == 0:
        return make_exception_response("1201", key)
    elif user.faction_id not in user.faction.guild.factions:
        return make_exception_response("4021", key)
    elif (
        str(user.faction_id) not in user.faction.guild.banking_config
        or user.faction.guild.banking_config[str(user.faction_id)]["channel"] == "0"
    ):
        return make_exception_response("0000", key, details={"message": "Faction vault configuration needs to be set."})

    withdrawal: Withdrawal = Withdrawal.new(
        user,
        validated_withdrawal_amount,
        withdrawal_option,
        timeout_datetime,
        discordpost=discordpost,
        discorddelete=discorddelete,
    )

    return withdrawal.to_dict(), 200, api_ratelimit_response(key)


@require_oauth(["faction:banking", "faction"])
@ratelimit
def all_requests(faction_id: int, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]
    now = int(datetime.datetime.utcnow().timestamp())

    if user is None:
        return make_exception_response("1100", key)
    elif user.faction is None:
        return make_exception_response("1102", key)
    elif user.faction_id != faction_id:
        return make_exception_response("4022", key)

    search_type = request.args.get("type", "pending")
    scope = request.args.get("scope", "user")

    try:
        limit = int(request.args.get("limit", 100))
    except (TypeError, ValueError):
        return make_exception_response(
            "1000", key, details={"message": "The request `limit` must be an integer between 1 and 100."}
        )

    try:
        before = int(request.args.get("before", now))
    except (TypeError, ValueError):
        return make_exception_response(
            "1000",
            key,
            details={"message": "The request `before` must be a UNIX timestamp less than the current timestamp."},
        )

    if search_type not in ("pending", "all"):
        return make_exception_response(
            "1000", key, details={"message": "The request `type` must be either `pending` or `all`."}
        )
    elif scope not in ("user", "faction"):
        return make_exception_response(
            "1000", key, details={"message": "The request `scope must be either `user` or `faction`."}
        )
    elif scope == "faction" and user.tid not in user.faction.get_bankers():
        return make_exception_response("4007", key)
    elif limit > 100 or limit <= 0:
        return make_exception_response(
            "1000", key, details={"message": "The request `limit` must be an integer between 1 and 100."}
        )
    elif before > now:
        return make_exception_response(
            "1000",
            key,
            details={"message": "The request `before` must be a UNIX timestamp less than the current timestamp."},
        )

    withdrawal_query = (
        Withdrawal.select()
        .where(Withdrawal.faction_tid == faction_id)
        .order_by(Withdrawal.time_requested.desc())
        .limit(limit)
    )

    if scope == "user":
        withdrawal_query.where(Withdrawal.requester == user.tid)
    if search_type == "pending":
        withdrawal_query = withdrawal_query.where(Withdrawal.status == 0)
    if before != now:
        withdrawal_query = withdrawal_query.where(Withdrawal.time_requested < before)

    return [withdrawal.to_dict() for withdrawal in withdrawal_query], 200, api_ratelimit_response(key)


@require_oauth(["faction:banking", "faction"])
@ratelimit
def cancel_request(faction_id: int, request_id: str, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]

    if user is None:
        return make_exception_response("1100", key)
    elif user.faction is None:
        return make_exception_response("1102", key)
    elif user.faction_id != faction_id:
        return make_exception_response("4022", key)
    elif user.faction.guild is None:
        return make_exception_response("1001", key)
    elif len(user.faction.aa_keys) == 0:
        return make_exception_response("1201", key)
    elif user.faction_id not in user.faction.guild.factions:
        return make_exception_response("4021", key)
    elif (
        str(user.faction_id) not in user.faction.guild.banking_config
        or user.faction.guild.banking_config[str(user.faction_id)]["channel"] == "0"
    ):
        return make_exception_response("0000", key, details={"message": "Faction vault configuration needs to be set."})

    withdrawal_query = Withdrawal.select().where(Withdrawal.faction_tid == faction_id)

    try:
        withdrawal_query = withdrawal_query.where(Withdrawal.guid == uuid.UUID(request_id))
    except ValueError:
        # If there is a value error, the request_id is the wid not the GUID as it isn't formatted as a UUID
        withdrawal_query = withdrawal_query.where(Withdrawal.wid == request_id)

    try:
        withdrawal: Withdrawal = withdrawal_query.get()
    except (DoesNotExist, DataError):
        return make_exception_response("1000", key)

    if withdrawal.status != 0:
        return make_exception_response(
            "0000",
            key,
            details={"message": "The request must be unfulfilled, but it has already been fulfilled or cancelled."},
        )
    elif withdrawal.requester != user.tid and user.tid not in user.faction.get_bankers():
        return make_exception_response("4007", key)

    withdrawal.cancel(user, discordpost=discordpost, discordpatch=discordpatch)

    return "", 204, api_ratelimit_response(key)
