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

from tornium_celery.tasks.api import discorddelete, discordpost
from tornium_commons.formatters import commas, discord_escaper, find_list, text_to_num
from tornium_commons.models import User, Withdrawal
from tornium_commons.skyutils import SKYNET_ERROR

from skynet.decorators import invoker_required, with_deferred_response


@invoker_required
@with_deferred_response
def withdraw(interaction, *args, **kwargs):
    user: User = kwargs["invoker"]

    if user is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Not Located",
                        "description": "No user was located for your Discord account. Please contact the developer",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Not Located",
                        "description": "Your faction could not be located in Tornium's database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction.guild is None or user.faction_id not in user.faction.guild.factions:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The server needs to be added to {discord_escaper(user.faction.name)}'s bot configuration and "
                        f"to the server. Please contact the server administrators for the faction's server to do this via "
                        f"[the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }
    elif (
        str(user.faction_id) not in user.faction.guild.banking_config
        or user.faction.guild.banking_config[str(user.faction_id)]["channel"] == "0"
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The banking channels needs to be set for {discord_escaper(user.faction.name)}. Please contact "
                        f"the server administrators to do this via [the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }

    # 0: cash (default)
    # 1: points
    withdrawal_option = find_list(interaction["data"]["options"], "name", "option")

    if withdrawal_option is None or withdrawal_option["value"] == "Cash":
        withdrawal_option_str = "money_balance"
    elif withdrawal_option["value"] == "Points":
        withdrawal_option_str = "points_balance"
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Withdrawal Request Failed",
                        "description": "An incorrect withdrawal type was passed.",
                        "color": SKYNET_ERROR,
                        "footer": {"text": f"Inputted withdrawal type: {withdrawal_option['value']}"},
                    }
                ],
                "flags": 64,
            },
        }

    timeout = find_list(interaction["data"]["options"], "name", "timeout")
    timeout_datetime: typing.Optional[datetime.datetime] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    if timeout is None:
        pass
    elif timeout["value"] == "15m":
        timeout_datetime = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    elif timeout["value"] == "30m":
        timeout_datetime = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    elif timeout["value"] == "2h":
        timeout_datetime = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    elif timeout["value"] == "4h":
        timeout_datetime = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    elif timeout["value"] == "8h":
        timeout_datetime = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    elif timeout["value"] == "none":
        timeout_datetime = None

    withdrawal_amount = find_list(interaction["data"]["options"], "name", "amount")

    if withdrawal_amount is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Parameters Passed",
                        "description": "No withdrawal amount was passed, but is required.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    withdrawal_amount = withdrawal_amount["value"]

    if isinstance(withdrawal_amount, str) and withdrawal_amount.lower() == "all":
        withdrawal_amount = "all"
    elif isinstance(withdrawal_amount, str):
        try:
            withdrawal_amount = text_to_num(withdrawal_amount)
        except ValueError:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Invalid Withdrawal Amount",
                            "description": f"You have tried to withdraw `{withdrawal_amount}`, but this is not a "
                            f"valid amount. For proper formatting, take a look at the "
                            f"[documentation](https://docs.tornium.com/en/latest/reference/bot-banking.html#withdraw-command)",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

    try:
        validated_withdrawal_amount = Withdrawal.has_sufficient_balance(
            user.tid, user.faction_id, withdrawal_amount, withdrawal_option_str
        )
        # Other errors will be handled by the overall error handler
    except ValueError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Withdrawal Request Failed",
                        "description": f"The withdrawal request failed. {str(e)}",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    withdrawal: Withdrawal = Withdrawal.new(
        user,
        validated_withdrawal_amount,
        withdrawal_option_str,
        timeout_datetime,
        discordpost=discordpost,
        discorddelete=discorddelete,
    )

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": f"Vault Request #{withdrawal.wid}",
                    "description": "Your vault request has been forwarded to the faction bankers. The request "
                    f"expires {'never' if timeout_datetime is None else f'<t:{int(timeout_datetime.timestamp())}:R>'}.",
                    "fields": [
                        {
                            "name": "Request Type",
                            "value": "Cash" if withdrawal_option_str == "money_balance" else "Points",
                        },
                        {"name": "Amount Requested", "value": commas(validated_withdrawal_amount)},
                    ],
                }
            ],
            "flags": 64,
        },
    }
