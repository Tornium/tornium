# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

import mongoengine.queryset
from bson.objectid import ObjectId
from mongoengine.queryset.visitor import Q

import redisdb
import tasks
import utils
from models.notificationmodel import NotificationModel
from models.usermodel import UserModel
from skynet.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO, get_admin_keys, invoker_exists


@invoker_exists
def notify(interaction, *args, **kwargs):
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
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        stock = stock[1]["value"]
        price = price[1]["value"]
        equality = equality[1]["value"]

        if private == -1:
            private = True
        else:
            private = private[1]["value"]

        if channel == -1:
            channel = None
        else:
            channel = channel[1]["value"]

        if price <= 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Command Input",
                            "description": "The stock price must be greater than zero.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
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
                    ],
                    "flags": 64,  # Ephemeral
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
                    ],
                    "flags": 64,  # Ephemeral
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
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        stocks: dict = redisdb.get_redis().json().get("tornium:stocks")

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
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
        elif stock not in stocks.values():
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Unknown Stock Acronym",
                            "description": f'"{stock}" does not match a stock acronym in the cache.',
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        stock_id = [a for a, value in stocks.items() if value == stock]

        if len(stock_id) != 1 or not stock_id[0].isdigit():
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Unknown Stock Acronym",
                            "description": f'"{stock}" does not match a stock acronym in the cache.',
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
        else:
            stock_id = int(stock_id[0])

        notification = NotificationModel(
            invoker=user.tid,
            time_created=utils.now(),
            recipient=user.discord_id if private else channel,
            recipient_type=int(not private),
            ntype=0,
            target=stock_id,
            persistent=False,
            value=price,
            options={"equality": equality},
        ).save()

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Stock Notification Created",
                        "description": "A stock notification has been created with the following configuration.",
                        "color": SKYNET_GOOD,
                        "fields": [
                            {
                                "name": "Private",
                                "value": not bool(notification.recipient_type),
                                "inline": True,
                            },
                            {
                                "name": "Target Channel",
                                "value": f"<#{notification.recipient}>"
                                if notification.recipient_type == 1
                                else "Direct Message",
                                "inline": True,
                            },
                            {
                                "name": "Stock",
                                "value": stock,
                                "inline": True,
                            },
                            {
                                "name": "Stock Price",
                                "value": f"${utils.commas(price)}",
                                "inline": True,
                            },
                            {
                                "name": "Equality",
                                "value": equality,
                                "inline": True,
                            },
                        ],
                        "footer": {
                            "text": f"DB ID: {notification.id}",
                        },
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    def delete():
        notification_id = utils.find_list(subcommand_data, "name", "notification")

        if notification_id == -1:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Not Yet Implemented",
                            "description": "This feature has not been implemented yet. Use `all` to delete all "
                            "notifications or use `/stocks notify list` to show the ID from which to "
                            "delete.",
                            "color": SKYNET_INFO,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

        notification_id = notification_id[1]["value"]
        notifications: mongoengine.queryset.QuerySet

        if notification_id.lower() == "all":
            notifications = NotificationModel.objects(invoker=user.tid)
        else:
            notifications = NotificationModel.objects(Q(_id=ObjectId(notification_id)) & Q(invoker=user.tid))

        if notifications.count() == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Notification Query Failed",
                            "description": "No notifications could be located with the passed parameters.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
        else:
            notification_count = notifications.count()

        notification: NotificationModel
        for notification in notifications:
            notification.delete()

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Notifications Deleted",
                        "description": f"{notification_count} matching notifications found and deleted.",
                        "color": SKYNET_GOOD,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    def list():
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Command Not Yet Implemented",
                        "description": "This command is currently under construction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if "member" in interaction:
        user: UserModel = UserModel.objects(discord_id=interaction["member"]["user"]["id"]).first()
    else:
        user: UserModel = UserModel.objects(discord_id=interaction["user"]["id"]).first()

    user: UserModel = kwargs["invoker"]

    try:
        subcommand = interaction["data"]["options"][0]["options"][0]["name"]
        subcommand_data = interaction["data"]["options"][0]["options"][0]["options"]
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
    elif subcommand == "list":
        return list()
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
                ],
                "flags": 64,  # Ephemeral
            },
        }
