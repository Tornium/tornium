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
import random
import typing
import uuid

from peewee import (
    BigIntegerField,
    BooleanField,
    DateTimeField,
    DoesNotExist,
    IntegerField,
    IntegrityError,
    SmallIntegerField,
    UUIDField,
)
from tornium_celery.tasks.api import discorddelete, discordpost

from tornium_commons.formatters import commas, discord_escaper
from tornium_commons.models import User

from ..errors import MissingKeyError
from .base_model import BaseModel
from .faction import Faction


class Withdrawal(BaseModel):
    wid = IntegerField(primary_key=True)
    guid = UUIDField(index=True)
    faction_tid = IntegerField(null=False)
    amount = BigIntegerField(null=False)
    cash_request = BooleanField(default=True)

    requester = IntegerField(null=False)
    time_requested = DateTimeField(null=False)
    expires_at = DateTimeField(default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=1), null=True)

    # Withdrawal status
    # 0: unfulfilled
    # 1: fulfilled
    # 2: cancelled
    # 3: cancelled by system
    status = SmallIntegerField()

    fulfiller = IntegerField(null=True)  # -1: someone
    time_fulfilled = DateTimeField(null=True)

    withdrawal_message = BigIntegerField()  # Discord message ID

    def to_dict(self) -> dict:
        return {
            "id": self.wid,
            "guid": str(self.guid),
            "user_id": self.requester,
            "faction_id": self.faction_tid,
            "amount": self.amount,
            "type": "money_balance" if self.cash_request else "points_balance",
            "expires_at": self.expires_at.timestamp(),
        }

    def has_sufficient_balance(
        user_id: int,
        faction_id: int,
        amount: int | typing.Literal["all"],
        request_type: typing.Literal["points_balance"] | typing.Literal["money_balance"],
    ) -> int:
        """
        Check if the requesting user has sufficient remaining in their faction balance. Returns the amount if the user has sufficient balance; throws a `ValueError` or
        any error from `tornget` if the user does not have a sufficient balance or if Tornium is unable to determine the user's balance.

        Their faction balance must be greater than the sum of existing, non-fulfilled withdrawal requests and this request.
        """

        from tornium_celery.tasks.api import tornget

        aa_keys = Faction.select().where(Faction.tid == faction_id).get().aa_keys

        if len(aa_keys) == 0:
            raise MissingKeyError()

        faction_balances = tornget(f"faction/{faction_id}?selections=donations", random.choice(aa_keys))["donations"]

        try:
            current_balance = faction_balances[str(user_id)][request_type]
        except (TypeError, ValueError):
            raise ValueError("Failed to parse Torn response. You may not have a balance in your faction.")

        if amount == "all" and current_balance <= 0:
            # The user needs to have any positive balance when requesting everything.
            raise ValueError("You do not have a balance in your faction.")
        elif isinstance(amount, int) and amount > current_balance:
            # The user is requesting more than they have in their balance
            raise ValueError("You do not have sufficient balance in your faction.")

        pending_user_withdrawals = Withdrawal.select(Withdrawal.amount).where(
            (Withdrawal.requester == user_id)
            & (Withdrawal.faction_tid == faction_id)
            & (Withdrawal.cash_request == (request_type == "money_balance"))
            & (Withdrawal.status == 0)
        )

        if len(pending_user_withdrawals) == 0:
            return current_balance if amount == "all" else amount
        elif amount == "all" and len(pending_user_withdrawals) != 0:
            # There must be no pending requests when requesting all the money in a user's balance.
            raise ValueError("There must be no pending requests when requesting all of your balance.")
        elif sum([withdrawal.amount for withdrawal in pending_user_withdrawals]) + amount > current_balance:
            raise ValueError("Your pending requests and your current requests will go over your balance.")

        return current_balance if amount == "all" else amount

    @classmethod
    def new(
        cls,
        user: User,
        amount: int,
        request_type: typing.Literal["points_balance"] | typing.Literal["money_balance"],
        timeout: typing.Optional[datetime.datetime],
    ):
        try:
            last_request = Withdrawal.select(Withdrawal.wid).order_by(-Withdrawal.wid).first()
            request_id = last_request.wid + 1
        except DoesNotExist:
            request_id = 0

        guid = uuid.uuid4().hex

        message_payload = {
            "embeds": [
                {
                    "title": f"Vault Request #{commas(request_id)}",
                    "description": f"{discord_escaper(user.name)} [{user.tid}] is requesting "
                    f"{commas(amount)} in {'points' if request_type == 'points_balance' else 'cash'} "
                    f"from the faction vault. The request expires {'never' if timeout is None else f'<t:{int(timeout.timestamp())}:R>'}.",
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
                }
            ],
        }

        for role in user.faction.guild.banking_config[str(user.faction_id)]["roles"]:
            if "content" not in message_payload:
                message_payload["content"] = ""

            message_payload["content"] += f"<@&{role}>"

        message = discordpost(
            f'channels/{user.faction.guild.banking_config[str(user.faction_id)]["channel"]}/messages',
            payload=message_payload,
        )

        try:
            withdrawal = Withdrawal.create(
                wid=request_id,
                guid=guid,
                faction_tid=user.faction_id,
                amount=amount,
                cash_request=request_type == "cash_request",
                requester=user.tid,
                time_requested=datetime.datetime.utcnow(),
                expires_at=timeout,
                status=0,
                fulfiller=None,
                time_fulfilled=None,
                withdrawal_message=message["id"],
            )
        except IntegrityError as e:
            discorddelete.delay(
                f"channels/{user.faction.guild.banking_config[str(user.faction_id)]['channel']}/messages/{message['id']}"
            ).forget()

            raise e

        return withdrawal
