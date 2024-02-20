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
import json
import random
import typing
import uuid

from flask import jsonify, request
from tornium_celery.tasks.api import discordpost, tornget
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.formatters import commas
from tornium_commons.models import Server, User, Withdrawal

from controllers.api.v1.decorators import authentication_required, ratelimit
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@authentication_required
@ratelimit
def vault_balance(*args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]

    if user.key is None:
        return make_exception_response("1200", None)

    if user.faction is None:
        update_user(key=user.key, tid=user.tid)

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


@authentication_required
@ratelimit
def banking_request(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = rds()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]
    amount_requested = data.get("amount_requested")

    if user.key is None:
        return make_exception_response("1200", None, redis_client=client)

    if amount_requested is None:
        return make_exception_response("1000", key, details={"element": "amount_requested"}, redis_client=client)
    elif amount_requested <= 0:
        return make_exception_response(
            "0000",
            key,
            details={"message": "Illegal amount requested."},
            redis_client=client,
        )

    if client.exists(f"tornium:banking-ratelimit:{user.tid}"):
        return make_exception_response("4292", key, redis_client=client)
    else:
        client.set(f"tornium:banking-ratelimit:{user.tid}", 1, ex=60)
        # TODO: Make this one redis call and check response

    amount_requested = str(amount_requested)

    if amount_requested.lower() != "all":
        amount_requested = int(amount_requested)
    else:
        amount_requested = "all"

    update_user(key=user.key, tid=user.tid)

    if user.faction is None:
        return make_exception_response("1102", key, redis_client=client)
    elif user.faction.guild is None:
        return make_exception_response("1001", key, redis_client=client)
    elif len(user.faction.aa_keys) == 0:
        return make_exception_response("1201", key, redis_client=client)

    server: Server = user.faction.guild

    if server is None:
        return make_exception_response("1001", key, redis_client=client)
    elif user.faction_id not in server.factions:
        return make_exception_response("4021", key, redis_client=client)

    if (
        str(user.faction_id) not in server.banking_config
        or server.banking_config[str(user.faction_id)]["channel"] == "0"
    ):
        return make_exception_response(
            "0000",
            key,
            details={"message": "Faction vault configuration needs to be set."},
            redis_client=client,
        )

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
            redis_client=client,
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

        last_request: typing.Optional[Withdrawal] = Withdrawal.select(Withdrawal.wid).order_by(-Withdrawal.wid).first()

        if last_request is None:
            request_id = 0
        else:
            request_id = last_request.wid + 1

        guid = uuid.uuid4().hex

        if amount_requested != "all":
            message_payload = {
                "embeds": [
                    {
                        "title": f"Vault Request #{request_id}",
                        "description": f"{user.name} [{user.tid}] is requesting {commas(amount_requested)} in "
                        f"cash from the faction vault.",
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
                                "url": f"https://tornium.com/faction/banking/fulfill/{guid}",
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
                    },
                ],
            }
        else:
            message_payload = {
                "embeds": [
                    {
                        "title": f"Vault Request #{request_id}",
                        "description": f"{user.name} [{user.tid}] is requesting "
                        f'{vault_balances["donations"][str(user.tid)]["money_balance"]} from the '
                        f"faction vault.",
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
                                "url": f"https://tornium.com/faction/banking/fulfill/{guid}",
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
                    },
                ],
            }

        for role in server.banking_config[str(user.faction_id)]["roles"]:
            if "content" not in message_payload:
                message_payload["content"] = ""

            message_payload["content"] += f"<@&{role}>"

        message = discordpost(
            f'channels/{server.banking_config[str(user.faction_id)]["channel"]}/messages',
            payload=message_payload,
            channel=server.banking_config[str(user.faction_id)]["channel"],
        )

        withdrawal = Withdrawal.create(
            wid=request_id,
            guid=guid,
            faction_tid=user.faction_id,
            amount=(
                amount_requested
                if amount_requested != "all"
                else vault_balances["donations"][str(user.tid)]["money_balance"]
            ),
            cash_request=True,
            requester=user.tid,
            status=0,
            time_requested=datetime.datetime.utcnow(),
            fulfiller=None,
            time_fulfilled=None,
            withdrawal_message=message["id"],
        )

        return (
            jsonify(
                {
                    "id": request_id,
                    "amount": withdrawal.amount,
                    "requester": user.tid,
                    "time_requested": withdrawal.time_requested,
                    "withdrawal_message": message["id"],
                }
            ),
            200,
            api_ratelimit_response(key),
        )
    else:
        return make_exception_response("1102", key, redis_client=client)
