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
import typing

from peewee import DoesNotExist
from tornium_commons import rds
from tornium_commons.formatters import commas, find_list
from tornium_commons.models import Notification, Server, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO


def notify(interaction, *args, **kwargs):
    def create():
        stock = find_list(subcommand_data, "name", "stock")
        price = find_list(subcommand_data, "name", "price")
        equality = find_list(subcommand_data, "name", "equality")
        private = find_list(subcommand_data, "name", "private")
        channel = find_list(subcommand_data, "name", "channel")

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
                    "flags": 64,
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
            private = False

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
                    "flags": 64,
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
                    "flags": 64,
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
                    "flags": 64,
                },
            }
        elif not private and ("member" not in interaction or "guild_id" not in interaction):
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
                    "flags": 64,
                },
            }

        if not private:
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

            if user.tid not in guild.admins:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Permission Denied",
                                "description": "You must be a server admin to run this command in this server. Please "
                                "try in another server where you admin or in a DM.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }

        stocks: dict = rds().json().get("tornium:stocks")

        if stocks is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Tornium Cache Error",
                            "description": "Tornium's cache does not currently include stocks. Please try again in a "
                            "few minutes. If this issue keeps occurring, please report it to the developer.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
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
                    "flags": 64,
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
                    "flags": 64,
                },
            }
        else:
            stock_id = int(stock_id[0])

        notification = Notification.insert(
            invoker=user.tid,
            time_created=datetime.datetime.utcnow(),
            recipient=user.discord_id if private else channel,
            recipient_guild=0 if private else int(interaction["guild_id"]),
            n_type=0,
            target=stock_id,
            persistent=False,
            enabled=True,
            options={"equality": equality, "value": price},
        ).execute()

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
                                "value": private,
                                "inline": True,
                            },
                            {
                                "name": "Target Channel",
                                "value": "Direct Message" if private else f"#{channel}",
                                "inline": True,
                            },
                            {
                                "name": "Stock",
                                "value": stock,
                                "inline": True,
                            },
                            {
                                "name": "Stock Price",
                                "value": f"${commas(price)}",
                                "inline": True,
                            },
                            {
                                "name": "Equality",
                                "value": equality,
                                "inline": True,
                            },
                        ],
                        "footer": {
                            "text": f"DB ID: {notification}",
                        },
                    }
                ],
                "flags": 64,
            },
        }

    def delete():
        notification_id = find_list(subcommand_data, "name", "notification")

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
                    "flags": 64,
                },
            }

        notification_id = notification_id[1]["value"]

        if notification_id.lower() == "all":
            notifications = Notification.select().where(Notification.invoker == user.tid)
        else:
            notifications = Notification.select().where(
                (Notification._id == notification_id) & (Notification.invoker == user.tid)
            )

        notification_count = notifications.count()

        if notification_count == 0:
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
                    "flags": 64,
                },
            }

        notification: Notification
        for notification in notifications:
            notification.delete_instance()

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
                "flags": 64,
            },
        }

    def list_stocks():
        page = find_list(subcommand_data, "name", "page")

        if page == -1:
            page = 0
        else:
            page = int(page[1]["value"])

        payload = {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "List of Notifications",
                        "description": f"{notifications[page * 9 : (page + 1) * 9].count()} notification(s) located...\n",
                        "color": SKYNET_INFO,
                        "fields": [],
                    }
                ],
                "flags": 64,
            },
        }

        stocks = rds().json().get("tornium:stocks")

        notification: Notification
        for notification in notifications[page * 9 : (page + 1) * 9]:
            payload["data"]["embeds"][0]["fields"].append(
                {
                    "name": f"{stocks[str(notification.target)]} {notification.options['equality']} ${commas(notification.options['value'], stock_price=True)} - {'DM' if notification.recipient_guild == 0 else f'<#{notification.recipient}>'}",
                    "value": f"DB ID: {notification.get_id()}",
                }
            )

        return payload

    # End of component functions

    user: User = kwargs["invoker"]

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
                "flags": 64,
            },
        }

    if subcommand != "initialize":
        guild: typing.Optional[Server]
        if "guild_id" in interaction:
            try:
                guild = Server.get_by_id(interaction["guild_id"])
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

            if user.tid not in guild.admins:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Permission Denied",
                                "description": "You must be an admin in this server to run this command. Run in a DM "
                                "or in a server where you are an admin.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }
        else:
            guild = None

        if subcommand not in ("create", "delete"):
            notifications = Notification.select().where(Notification.n_type == 0)

            if guild is not None:
                notifications = notifications.where(
                    (Notification.recipient_guild == guild.sid)
                    | ((Notification.recipient_guild == 0) & (Notification.invoker == user.tid))
                )
            else:
                notifications = notifications.where(
                    (Notification.recipient_guild == 0) & (Notification.invoker == user.tid)
                )

            if notifications.count() == 0:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "No Notification Found",
                                "description": "No notifications could be located with the passed parameters.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flag": 64,
                    },
                }

    if subcommand == "create":
        return create()
    elif subcommand == "delete":
        return delete()
    elif subcommand == "list":
        return list_stocks()
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
                "flags": 64,
            },
        }
