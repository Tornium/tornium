# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import json

from flask import jsonify, request

from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.faction import Faction
from models.server import Server
from models.user import User
from models.withdrawalmodel import WithdrawalModel
import redisdb
import tasks
import utils


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:banking", "read:faction", "faction:admin"})
def vault_balance(*args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user = User(kwargs["user"].tid)

    if user.factiontid == 0:
        user.refresh(force=True)

        if user.factiontid == 0:
            return make_exception_response("1102", key)

    faction = Faction(user.factiontid, key=user.key)
    faction_key = faction.rand_key()

    if faction_key is None:
        return make_exception_response("1201", key)

    try:
        vault_balances = tasks.tornget("faction/?selections=donations", faction.rand_key())
    except utils.TornError as e:
        return make_exception_response(
            "4100",
            key,
            details={
                "code": e.code,
                "error": e.error,
                "message": e.message,
            },
        )

    if str(user.tid) in vault_balances["donations"]:
        return (
            jsonify(
                {
                    "player_id": user.tid,
                    "faction_id": faction.tid,
                    "money_balance": vault_balances["donations"][str(user.tid)]["money_balance"],
                    "points_balance": vault_balances["donations"][str(user.tid)]["points_balance"],
                }
            ),
            200,
            api_ratelimit_response(key),
        )
    else:
        return make_exception_response("1100", key)


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "write:banking", "write:faction", "faction:admin"})
def banking_request(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user = User(kwargs["user"].tid)
    amount_requested = data.get("amount_requested")

    if amount_requested is None:
        return make_exception_response("1000", key, details={"element": "amount_requested"}, redis_client=client)
    elif amount_requested <= 0:
        return make_exception_response(
            "0000",
            key,
            details={"message": "Illegal amount requested."},
            redis_client=client,
        )

    if client.get(f"tornium:banking-ratelimit:{user.tid}") is not None:
        return make_exception_response("4292", key, redis_client=client)
    else:
        client.set(f"tornium:banking-ratelimit:{user.tid}", 1)
        client.expire(f"tornium:banking-ratelimit:{user.tid}", 60)

    amount_requested = str(amount_requested)

    if amount_requested.lower() != "all":
        amount_requested = int(amount_requested)
    else:
        amount_requested = "all"

    user.refresh()

    if user.factiontid == 0:
        user.refresh(force=True)

        if user.factiontid == 0:
            return make_exception_response("1102", key, redis_client=client)

    faction = Faction(user.factiontid, key=user.key)

    if faction.guild == 0:
        return make_exception_response("1001", key, redis_client=client)

    server = Server(faction.guild)

    if faction.tid not in server.factions:
        return make_exception_response("4021", key, redis_client=client)

    vault_config = faction.vault_config
    config = faction.config

    if vault_config.get("banking") == 0 or vault_config.get("banker") == 0 or config.get("vault") == 0:
        return make_exception_response(
            "0000",
            key,
            details={"message": "Faction vault configuration needs to be set."},
            redis_client=client,
        )

    try:
        vault_balances = tasks.tornget("faction/?selections=donations", faction.rand_key())
    except utils.TornError as e:
        return make_exception_response(
            "4100",
            key,
            details={
                "code": e.code,
                "error": e.error,
                "message": e.message,
            },
            redis_client=client,
        )

    if str(user.tid) in vault_balances["donations"]:
        if amount_requested != "all" and amount_requested > vault_balances["donations"][str(user.tid)]["money_balance"]:
            return make_exception_response(
                "0000",
                key,
                details={"message": "Illegal amount requested."},
                redis_client=client,
            )
        elif amount_requested == "all" and vault_balances["donations"][str(user.tid)]["money_balance"] <= 0:
            return make_exception_response(
                "0000",
                key,
                details={"message": "Illegal amount requested."},
                redis_client=client,
            )

        request_id = WithdrawalModel.objects().count()
        send_link = f"https://tornium.com/faction/banking/fulfill/{request_id}"

        if amount_requested != "all":
            message_payload = {
                "content": f'<@&{vault_config["banker"]}>',
                "embeds": [
                    {
                        "title": f"Vault Request #{request_id}",
                        "description": f"{user.name} [{user.tid}] is requesting {utils.commas(amount_requested)} in "
                        f"cash from the faction vault. "
                        f"To fulfill this request, enter `?f {request_id}` in this channel.",
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
                                "url": send_link,
                            },
                            {
                                "type": 2,
                                "style": 3,
                                "label": "Fulfill Manually",
                                "custom_id": "faction:vault:fulfill",
                            },
                        ],
                    },
                ],
            }
        else:
            message_payload = {
                "content": f'<@&{vault_config["banker"]}>',
                "embeds": [
                    {
                        "title": f"Vault Request #{request_id}",
                        "description": f"{user.name} [{user.tid}] is requesting "
                        f'{vault_balances["donations"][str(user.tid)]["money_balance"]} from the '
                        f"faction vault. "
                        f"To fulfill this request, enter `?f {request_id}` in this channel.",
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
                                "url": send_link,
                            },
                            {
                                "type": 2,
                                "style": 3,
                                "label": "Fulfill Manually",
                                "custom_id": "faction:vault:fulfill",
                            },
                        ],
                    },
                ],
            }
        message = tasks.discordpost(
            f'channels/{vault_config["banking"]}/messages',
            payload=message_payload,
        )

        withdrawal = WithdrawalModel(
            wid=request_id,
            amount=amount_requested
            if amount_requested != "all"
            else vault_balances["donations"][str(user.tid)]["money_balance"],
            requester=user.tid,
            factiontid=user.factiontid,
            time_requested=utils.now(),
            fulfiller=0,
            time_fulfilled=0,
            withdrawal_message=message["id"],
            wtype=0,
        )
        withdrawal.save()

        return (
            jsonify(
                {
                    "id": request_id,
                    "amount": withdrawal.amount,
                    "requester": user.tid,
                    "timerequested": withdrawal.time_requested,
                    "withdrawalmessage": message["id"],
                }
            ),
            200,
            api_ratelimit_response(key),
        )
    else:
        return make_exception_response("1102", key, redis_client=client)
