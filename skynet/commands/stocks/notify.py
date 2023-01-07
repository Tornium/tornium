# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from models.notificationmodel import NotificationModel
from models.usermodel import UserModel
import redisdb
from skynet.skyutils import get_admin_keys, SKYNET_ERROR, SKYNET_GOOD
import tasks
import utils


def notify(interaction):
    def create():
        stock = utils.find_list(subcommand_data, "name", "stock")
        price = utils.find_list(subcommand_data, "name", "price")
        equality = utils.find_list(subcommand_data, "name", "equality")
        private = utils.find_list(subcommand_data, "name", "private")
        channel = utils.find_list(subcommand_data, "name", "channel")

        if stock == -1 or price == -1:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Command Input",
                            "description": "A stock, stock price, and equality must be provided.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }
        elif price <= 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Command Input",
                            "description": "The stock price must be greater than zero.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }

        stock = stock[1]["value"]
        price = price[1]["value"]
        equality = equality[1]["value"]

        if private == -1:
            private = False
        else:
            private = private[1]["value"]

        if channel == -1:
            channel = None
        else:
            channel = channel[1]["value"]

        if equality == -1:
            equality = "="
        else:
            equality = equality[1]["value"]

        if not private and channel is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Command Input",
                            "description": "The notification can not be public without a channel provided.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }
        elif private and user.discord_id == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Verification Required",
                            "description": "Verification is required for private notifications.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }
        elif not private and "member" not in interaction:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Command Input",
                            "description": "The command must be run in a server for a channel to be passed.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }

        client = redisdb.get_redis()
        stocks = client.get("tornium:stocks")

        if stocks is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Tornium Cache Error",
                            "description": "Tornium's cache does not currently include stocks. Please try again in a "
                            "bit. If this issue keeps occurring, please report it to the developer.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }
        elif stock not in stocks:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Unknown Stock Acronym",
                            "description": f'"{stock}" does not match a stock acronym in the cache.',
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }

        notification = NotificationModel(
            invoker=user.tid,
            time_created=utils.now(),
            recipient=user.discord_id if private else channel,
            recipient_type=int(not private),
            ntype=0,
            target=stock,
            persistent=False,
            value=price,
            options={"equality": equality},
        )

        return {
            "type": 4,
            "data": [
                {
                    "embeds": [
                        {
                            "title": "Notification Created",
                            "description": "A stock notification has been created with the following configuration.",
                            "fields": [
                                {
                                    "name": "Private",
                                    "value": not bool(notification.recipient_type),
                                },
                                {
                                    "name": "Target Channel",
                                    "value": f"<#{notification.recipient}>"
                                    if notification.recipient_type == 1
                                    else "Direct Message",
                                },
                                {
                                    "name": "Stock",
                                    "value": notification.target,
                                },
                                {
                                    "name": "Stock Price",
                                    "value": notification.value,
                                },
                                {
                                    "name": "Equality",
                                    "value": notification.options["equality"],
                                },
                            ],
                            "color": SKYNET_GOOD,
                            "footer": {
                                "text": f"DB ID: {notification.id}",
                            },
                        }
                    ]
                }
            ],
        }

    def delete():
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Sub-Command Not Implemented",
                        "description": "This command hasn't been implemented yet.",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }

    if "member" in interaction:
        user: UserModel = UserModel.objects(discord_id=interaction["member"]["user"]["id"]).first()
    else:
        user: UserModel = UserModel.objects(discord_id=interaction["user"]["id"]).first()

    if user is None:
        admin_keys = get_admin_keys(interaction)

        if len(admin_keys) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No API Keys",
                            "description": "No API keys were found to be run for this command. Please sign into "
                            "Tornium or run this command in a server with signed-in admins.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        try:
            user_data = tasks.tornget(
                f"user/{interaction['member']['user']['id']}?selections=profile,discord",
                random.choice(admin_keys),
            )
        except utils.TornError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Torn API Error",
                            "description": f'The Torn API has raised error code {e.code}: "{e.message}".',
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
        except utils.NetworkingError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "HTTP Error",
                            "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        user: UserModel = UserModel.objects(tid=user_data["player_id"]).modify(
            upsert=True,
            new=True,
            set__name=user_data["name"],
            set__level=user_data["level"],
            set__last_refresh=utils.now(),
            set__discord_id=user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0,
            set__factionid=user_data["faction"]["faction_id"],
            set__status=user_data["last_action"]["status"],
            set__last_action=user_data["last_action"]["timestamp"],
        )

        if user.discord_id == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "User Requires Verification",
                            "description": "You are required to be verified officially by Torn through the "
                            "[official Torn Discord server](https://www.torn.com/discord] before being "
                            "able to utilize the banking features of this bot. Alternatively, you can "
                            "sign into [the web dashboard](https://tornium.com/faction/banking) with "
                            "your API key to send a request without verifying. If you have recently "
                            "verified yourself, please wait a minute or two before trying again.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
    elif user.tid == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Requires Verification",
                        "description": "You are required to be verified officially by Torn through the "
                        "[official Torn Discord server](https://www.torn.com/discord] before being "
                        "able to utilize the banking features of this bot. Alternatively, you can "
                        "sign into [the web dashboard](https://tornium.com/faction/banking) with "
                        "your API key to send a request without verifying. If you have recently "
                        "verified yourself, please wait a minute or two before trying again.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    try:
        subcommand = interaction["data"]["options"]["options"]["name"]
        subcommand_data = interaction["data"]["options"]["options"]["options"]
    except Exception:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Interaction Format",
                        "description": "Discord has returned an invalidly formatted interaction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if subcommand == "create":
        return create()
    elif subcommand == "delete":
        return delete()
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Command Not Found",
                        "description": "This command does not exist.",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }
