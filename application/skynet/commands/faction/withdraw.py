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
import uuid

from peewee import DoesNotExist, IntegrityError
from tornium_celery.tasks.api import discorddelete, discordpatch, discordpost, tornget
from tornium_commons import rds
from tornium_commons.formatters import commas, discord_escaper, find_list, text_to_num
from tornium_commons.models import Server, User, Withdrawal
from tornium_commons.skyutils import SKYNET_ERROR

from skynet.decorators import invoker_required
from skynet.skyutils import get_faction_keys


@invoker_required
def withdraw(interaction, *args, **kwargs):
    def followup_return(response):
        discordpatch("webhooks/{interaction['application_id']}/{interaction['token']}/messages/@original", response)
        return

    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Allowed",
                        "description": "This command can not be run in a DM (for now).",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif "options" not in interaction["data"]:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Options Required",
                        "description": "This command requires that options be passed.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        guild: Server = Server.get_by_id(interaction["guild_id"])
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Not Located",
                        "description": "This server could not be located in Tornium's database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

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
    elif user.faction_id not in guild.factions or user.faction.guild_id != guild.sid:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Configuration Required",
                        "description": f"The server needs to be added to {discord_escaper(user.faction.name)}'s bot configuration and "
                        f"to the server. Please contact the server administrators to do this via "
                        f"[the dashboard](https://tornium.com).",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }
    elif (
        str(user.faction_id) not in guild.banking_config or guild.banking_config[str(user.faction_id)]["channel"] == "0"
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
        withdrawal_option = 0
    elif withdrawal_option["value"] == "Points":
        withdrawal_option = 1
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

    client = rds()
    # TODO: Make this set of redis queries atomic
    if client.exists(f"tornium:banking-ratelimit:{user.tid}"):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Ratelimit Reached",
                        "description": f"You have reached the ratelimit on banking requests (once every minute). "
                        f"Please try again in {client.ttl(f'tornium:banking-ratelimit:{user.tid}')} seconds.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    else:
        client.set(f"tornium:banking-ratelimit:{user.tid}", 1)
        client.expire(f"tornium:banking-ratelimit:{user.tid}", 60)

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

    if isinstance(withdrawal_amount, str):
        if withdrawal_amount.lower() == "all":
            withdrawal_amount = "all"
        else:
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
                                f"[documentation](https://docs.tornium.com/en/latest/user/bot/banking.html#withdraw)",
                            }
                        ],
                        "flags": 64,
                    },
                }

    aa_keys = get_faction_keys(interaction, user.faction)

    if len(aa_keys) == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Keys",
                        "description": "No AA API keys were found to be run for this command. Please sign into "
                        "Tornium or ask a faction AA member to sign into Tornium.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    # Creating a followup message is necessary due to increased Torn and Discord API latencies
    # causing sometimes frequent client-side timeouts of withdrawal slash commands.
    discordpost(f"interactions/{interaction['id']}/{interaction['token']}/callback", {"type": 5})

    faction_balances = tornget("faction/?selections=donations", random.choice(aa_keys))["donations"]

    if str(user.tid) not in faction_balances:
        followup_return(
            {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Faction Error",
                            "description": (
                                f"{discord_escaper(user.name)} [{user.tid}] is not in {user.faction.name}'s donations list. This may "
                                f"indicate that they are not in the faction or that they don't have any funds in the "
                                f"faction vault."
                            ),
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        )
        return {}

    if withdrawal_option == 1:
        withdrawal_option_str = "points_balance"
    else:
        withdrawal_option_str = "money_balance"

    if withdrawal_amount != "all" and withdrawal_amount > faction_balances[str(user.tid)][withdrawal_option_str]:
        followup_return(
            {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Not Enough",
                            "description": "You do not have enough of the requested currency in the faction vault.",
                            "fields": [
                                {"name": "Amount Requested", "value": withdrawal_amount},
                                {
                                    "name": "Amount Available",
                                    "value": faction_balances[str(user.tid)][withdrawal_option_str],
                                },
                            ],
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        )
        return {}
    elif withdrawal_amount == "all" and faction_balances[str(user.tid)][withdrawal_option_str] <= 0:
        followup_return(
            {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Not Enough",
                            "description": "You have requested all of your currency, but have zero or a negative vault "
                            "balance.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        )
        return {}

    last_request = Withdrawal.select(Withdrawal.wid).order_by(-Withdrawal.wid).first()

    if last_request is None:
        request_id = 0
    else:
        request_id = last_request.wid + 1

    guid = uuid.uuid4().hex

    if withdrawal_amount != "all":
        message_payload = {
            "embeds": [
                {
                    "title": f"Vault Request #{request_id}",
                    "description": f"{discord_escaper(user.name)} [{user.tid}] is requesting {commas(withdrawal_amount)} "
                    f"in {'points' if withdrawal_option == 1 else 'cash'}"
                    f" from the faction vault.",
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
    else:
        message_payload = {
            "embeds": [
                {
                    "title": f"Vault Request #{request_id}",
                    "description": f"{discord_escaper(user.name)} [{user.tid}] is requesting "
                    f"{commas(faction_balances[str(user.tid)][withdrawal_option_str])} in "
                    f"{'points' if withdrawal_option == 1 else 'cash'}"
                    f" from the faction vault.",
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

    for role in guild.banking_config[str(user.faction_id)]["roles"]:
        if "content" not in message_payload:
            message_payload["content"] = ""

        message_payload["content"] += f"<@&{role}>"

    message = discordpost(
        f'channels/{guild.banking_config[str(user.faction_id)]["channel"]}/messages',
        payload=message_payload,
    )

    try:
        Withdrawal.create(
            wid=request_id,
            guid=guid,
            faction_tid=user.faction_id,
            amount=(
                withdrawal_amount
                if withdrawal_amount != "all"
                else faction_balances[str(user.tid)][withdrawal_option_str]
            ),
            cash_request=not bool(withdrawal_option),
            requester=user.tid,
            time_requested=datetime.datetime.utcnow(),
            status=0,
            fulfiller=None,
            time_fulfilled=None,
            withdrawal_message=message["id"],
        )
    except IntegrityError:
        discorddelete.delay(
            f"channels/{guild.banking_config[str(user.faction_id)]['channel']}/messages/{message['id']}"
        ).forget()

        followup_return(
            {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Withdrawal Failure",
                            "description": "The withdrawal has failed due to an internal integrity error. Please try again and if this error repeatedly occurs, please contact the developer.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        )
        return {}

    followup_return(
        {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": f"Vault Request #{request_id}",
                        "description": "Your vault request has been forwarded to the faction leadership.",
                        "fields": [
                            {
                                "name": "Request Type",
                                "value": "Cash" if withdrawal_option == 0 else "Points",
                            },
                            {"name": "Amount Requested", "value": withdrawal_amount},
                        ],
                    }
                ],
                "flags": 64,
            },
        }
    )
    return {}
