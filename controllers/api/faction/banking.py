# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json

from honeybadger import honeybadger

from controllers.api.decorators import *
from models.faction import Faction
from models.server import Server
from models.user import User
from models.withdrawalmodel import WithdrawalModel
import tasks
import utils


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:banking", "read:faction", "faction:admin"})
def vault_balance(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user = User(kwargs["user"].tid)

    if user.factiontid == 0:
        user.refresh(force=True)

        if user.factiontid == 0:
            return (
                jsonify(
                    {
                        "code": 0,
                        "name": "GeneralError",
                        "message": "Server failed to fulfill the request. The API key's user is required to be in a Torn "
                        "faction.",
                    }
                ),
                400,
                {
                    "X-RateLimit-Limit": 250,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )

    faction = Faction(user.factiontid, key=user.key)
    faction_key = faction.rand_key()

    if faction_key is None:
        return jsonify(
            {
                "code": 0,
                "name": "GeneralError",
                "message": "Server failed to fulfill the request. The user's faction does not have any signed in AA members.",
            },
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit_Reset": client.ttl(key),
            },
        )

    try:
        vault_balances = tasks.tornget(
            f"faction/?selections=donations", faction.rand_key()
        )
    except utils.TornError as e:
        honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})

        return (
            jsonify(
                {
                    "code": 4100,
                    "name": "TornError",
                    "message": "Server failed to fulfill the request. The Torn API has returned an error.",
                    "error": {"code": e.code, "error": e.error, "message": e.message},
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    if str(user.tid) in vault_balances["donations"]:
        return (
            jsonify(
                {
                    "player_id": user.tid,
                    "faction_id": faction.tid,
                    "money_balance": vault_balances["donations"][str(user.tid)][
                        "money_balance"
                    ],
                    "points_balance": vault_balances["donations"][str(user.tid)][
                        "points_balance"
                    ],
                }
            ),
            200,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    else:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownUser",
                    "message": "Server failed to fulfill the request. The user was not found in the faction's vault records.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )


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
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. There was no amount requested provided but an amount "
                    "requested was required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif amount_requested <= 0:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The amount requested was less than zero, but must be greater than zero.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    if client.get(f"tornium:banking-ratelimit:{user.tid}") is not None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The user has reached their banking ratelimit.",
                }
            ),
            429,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
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
            return (
                jsonify(
                    {
                        "code": 0,
                        "name": "GeneralError",
                        "message": "Server failed to fulfill the request. The API key's user is required to be in a Torn "
                        "faction.",
                    }
                ),
                400,
                {
                    "X-RateLimit-Limit": 250,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )

    faction = Faction(user.factiontid, key=user.key)

    if faction.guild == 0:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The faction does not currently have a Discord server set.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    server = Server(faction.guild)

    if faction.tid not in server.factions:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The user's faction is not in the stored server's list "
                    "of factions.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    vault_config = faction.vault_config
    config = faction.config

    if (
        vault_config.get("banking") == 0
        or vault_config.get("banker") == 0
        or config.get("vault") == 0
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The user's faction's bot configuration needs to be "
                    "configured by faction AA members.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    try:
        vault_balances = tasks.tornget(
            f"faction/?selections=donations", faction.rand_key()
        )
    except utils.TornError as e:
        honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})

        return (
            jsonify(
                {
                    "code": 4100,
                    "name": "TornError",
                    "message": "Server failed to fulfill the request. The Torn API has returned an error.",
                    "error": {"code": e.code, "error": e.error, "message": e.message},
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    if str(user.tid) in vault_balances["donations"]:
        if (
            amount_requested != "all"
            and amount_requested
            > vault_balances["donations"][str(user.tid)]["money_balance"]
        ):
            return (
                jsonify(
                    {
                        "code": 0,
                        "name": "GeneralError",
                        "message": "Server failed to fulfill the request. The amount requested was greater than the amount in "
                        "the user's faction vault balance.",
                    }
                ),
                400,
                {
                    "X-RateLimit-Limit": 250,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )
        elif (
            amount_requested == "all"
            and vault_balances["donations"][str(user.tid)]["money_balance"] <= 0
        ):
            return (
                jsonify(
                    {
                        "code": 0,
                        "name": "GeneralError",
                        "message": "Server failed to fulfill the request. The user has no cash in the faction vault or a "
                        "negative vault balance.",
                    }
                ),
                400,
                {
                    "X-RateLimit-Limit": 250,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )

        request_id = WithdrawalModel.objects().count()
        send_link = f"https://tornium.com/faction/banking/fulfill/{request_id}"

        if amount_requested != "all":
            message_payload = {
                "content": f'<@&{vault_config["banker"]}>',
                "embeds": [
                    {
                        "title": f"Vault Request #{request_id}",
                        "description": f"{user.name} [{user.tid}] is requesting {utils.commas(amount_requested)} in cash from the "
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
            dev=server.skynet,
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
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    else:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownFaction",
                    "message": "Server failed to fulfill the request. There was no faction stored with that faction ID.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
