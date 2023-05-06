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
import time
import uuid

from flask import jsonify, request
from tornium_celery.tasks.api import discordpost, tornget
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.formatters import commas
from tornium_commons.models import FactionModel, ServerModel, UserModel, WithdrawalModel

from controllers.api.decorators import authentication_required, ratelimit
from controllers.api.utils import api_ratelimit_response, make_exception_response


@authentication_required
@ratelimit
def vault_balance(*args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: UserModel = kwargs["user"]

    if user.factionid == 0:
        update_user(key=user.key, tid=user.tid).get()
        user.reload()

        if user.factionid == 0:
            return make_exception_response("1102", key)

    faction: FactionModel = FactionModel.objects(tid=user.factionid).first()

    if faction is None:
        return make_exception_response("1102", key)

    if len(faction.aa_keys) == 0:
        return make_exception_response("1201", key)

    try:
        vault_balances = tornget("faction/?selections=donations", random.choice(faction.aa_keys))
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


@authentication_required
@ratelimit
def banking_request(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = rds()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: UserModel = kwargs["user"]
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

    if client.exists(f"tornium:banking-ratelimit:{user.tid}"):
        return make_exception_response("4292", key, redis_client=client)
    else:
        client.set(f"tornium:banking-ratelimit:{user.tid}", 1)
        client.expire(f"tornium:banking-ratelimit:{user.tid}", 60)

    amount_requested = str(amount_requested)

    if amount_requested.lower() != "all":
        amount_requested = int(amount_requested)
    else:
        amount_requested = "all"

    update_user(key=user.key, tid=user.tid).get()
    user.reload()

    if user.factionid == 0:
        return make_exception_response("1102", key, redis_client=client)

    faction: FactionModel = FactionModel.objects(tid=user.factionid).first()

    if faction is None:
        return make_exception_response("1102", key, redis_client=client)
    elif faction.guild == 0:
        return make_exception_response("1001", key, redis_client=client)
    elif len(faction.aa_keys) == 0:
        return make_exception_response("1201", key, redis_client=client)

    server: ServerModel = ServerModel.objects(sid=faction.guild).first()

    if server is None:
        return make_exception_response("1001", key, redis_client=client)
    elif faction.tid not in server.factions:
        return make_exception_response("4021", key, redis_client=client)

    if str(faction.tid) not in server.banking_config or server.banking_config[str(faction.tid)]["channel"] == "0":
        return make_exception_response(
            "0000",
            key,
            details={"message": "Faction vault configuration needs to be set."},
            redis_client=client,
        )

    try:
        vault_balances = tornget("faction/?selections=donations", random.choice(faction.aa_keys))
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

        request_id = WithdrawalModel.objects().count()
        guid = uuid.uuid4().hex
        send_link = f"https://tornium.com/faction/banking/fulfill/{guid}"

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
                                "url": send_link,
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
                                "url": send_link,
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

        for role in server.banking_config[str(faction.tid)]["roles"]:
            if "content" not in message_payload:
                message_payload["content"] = ""

            message_payload["content"] += f"<@&{role}>"

        message = discordpost(
            f'channels/{server.banking_config[str(faction.tid)]["channel"]}/messages',
            payload=message_payload,
        )

        withdrawal = WithdrawalModel(
            wid=request_id,
            guid=guid,
            amount=amount_requested
            if amount_requested != "all"
            else vault_balances["donations"][str(user.tid)]["money_balance"],
            requester=user.tid,
            factiontid=user.factionid,
            time_requested=int(time.time()),
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
                    "time_requested": withdrawal.time_requested,
                    "withdrawal_message": message["id"],
                }
            ),
            200,
            api_ratelimit_response(key),
        )
    else:
        return make_exception_response("1102", key, redis_client=client)
