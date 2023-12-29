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
import random
import typing

import celery
from celery.utils.log import get_task_logger
from tornium_commons import rds
from tornium_commons.formatters import commas, torn_timestamp
from tornium_commons.models import Item, Notification, Server, User
from tornium_commons.skyutils import SKYNET_INFO

from .api import tornget
from .stakeout_hooks import send_notification

logger = get_task_logger("celery_app")


@celery.shared_task(
    name="tasks.items.update_items",
    routing_key="default.items.update_items",
    queue="default",
    time_limit=15,
)
def update_items(items_data):
    Item.update_items(torn_get=tornget, key=User.random_key())

    rds().set(
        "tornium:items:last-update",
        int(datetime.datetime.utcnow().timestamp()),
        ex=5400,
    )  # 1.5 hours


@celery.shared_task(
    name="tasks.items.fetch_market",
    routing_key="default.items.fetch_market",
    queue="default",
    time_limit=15,
)
def fetch_market():
    notifications = Notification.select().where((Notification.n_type == 3) & (Notification.enabled == True))
    unique_items = list(notifications.distinct(Notification.target))

    unique_notif: Notification
    for unique_notif in unique_items:
        if unique_notif.recipient_guild == 0:
            recipient = unique_notif.recipient
            key_user: typing.Optional[User] = User.select(User.key).where(User.discord_id == recipient).first()

            if key_user is None:
                unique_notif.delete_instance()
                continue
        else:
            recipient = unique_notif.recipient_guild
            guild: typing.Optional[Server] = Server.select(Server.admins).where(Server.sid == recipient).first()

            if guild is None:
                unique_notif.delete_instance()
                continue

            key_user: typing.Optional[User] = (
                User.select(User.key).where(User.tid == random.choice(guild.admins)).first()
            )

        if key_user is None:
            continue
        elif key_user.key in ("", None):
            continue

        tornget.signature(
            kwargs={
                "endpoint": f"market/{unique_notif.target}?selections=itemmarket,bazaar",
                "key": key_user.key,
            },
            queue="api",
        ).apply_async(expires=300, link=market_notifications.signature(kwargs={"item_id": unique_notif.target}))


@celery.shared_task(
    name="tasks.items.market_notifications",
    routing_key="default.items.market_notifications",
    queue="default",
    time_limit=15,
)
def market_notifications(market_data: dict, item_id: int):
    if (market_data.get("itemmarket") is None or len(market_data.get("itemmarket", [])) == 0) and (
        market_data.get("bazaar") is None or len(market_data.get("bazaar", [])) == 0
    ):
        return

    notifications = Notification.select().where(
        (Notification.n_type == 3) & (Notification.enabled == True) & (Notification.target == item_id)
    )

    if notifications.count() == 0:
        return

    item: Item = Item.select().where(Item.tid == item_id).get()

    components = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "style": 5,
                    "label": "Item Market",
                    "url": f"https://www.torn.com/imarket.php#/p=shop&step=shop&type=&searchname={item_id}",
                }
            ],
        }
    ]

    percent_enabled: bool = any(n.options["type"] == "percent" for n in notifications)
    price_enabled: bool = any(n.options["type"] == "price" for n in notifications)
    quantity_enabled: bool = any(n.options["type"] == "quantity" for n in notifications)
    redis_client = rds()

    if market_data.get("itemmarket") is None:
        market_data["itemmarket"] = []
    if market_data.get("bazaar") is None:
        market_data["bazaar"] = []

    if not redis_client.exists(f"tornium:items:{item.tid}:ids"):
        market_ids = [listing["ID"] for listing in market_data["itemmarket"] + market_data["bazaar"]]

        if len(market_ids) != 0:
            redis_client.sadd(f"tornium:items:{item.tid}:ids", *market_ids)
        return

    item_ids = redis_client.smembers(f"tornium:items:{item.tid}:ids")

    if percent_enabled:
        notifications_map = {}

        for listing in market_data["itemmarket"] + market_data["bazaar"]:
            if listing["cost"] >= item.market_value:
                continue
            elif str(listing["ID"]) in item_ids:
                continue

            percent_change = abs(listing["cost"] - item.market_value) / item.market_value * 100

            n: Notification
            for n in notifications:
                if n.options["type"] != "percent" or n.options["value"] > percent_change:
                    continue

                if n.get_id() not in notifications:
                    notifications_map[n.get_id()] = []

                notifications_map[n.get_id()].append(
                    {
                        "cost": listing["cost"],
                        "quantity": listing["quantity"],
                        "percent_change": percent_change,
                    }
                )

        n: Notification
        for n in notifications:
            if n.get_id() not in notifications_map:
                continue

            fields = []
            i = 1
            total_quantity = 0

            for listing in notifications_map[n.get_id()]:
                fields.append(
                    {
                        "name": f"Bazaar #{i}",
                        "value": f"{commas(listing['quantity'])}x @ ${commas(listing['cost'])} → {commas(listing['quantity'] * listing['cost'])} @ -{listing['percent_change']}%",
                        "inline": True,
                    }
                )
                total_quantity += listing["quantity"]
                i += 1

            send_notification(
                n,
                payload={
                    "embeds": [
                        {
                            "title": f"{item.name} Percent Change Notification",
                            "description": f"{commas(total_quantity)}x of {item.name} have been found in {i - 1} bazaar(s) or market listing(s).",
                            "fields": fields,
                            "color": SKYNET_INFO,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": torn_timestamp()},
                        }
                    ],
                    "components": components,
                },
            )

    if price_enabled:
        notifications_map = {}

        for listing in market_data["itemmarket"] + market_data["bazaar"]:
            if str(listing["ID"]) in item_ids:
                continue

            for n in notifications:
                if n.options["type"] != "price" or listing["cost"] >= n.options["value"]:
                    continue

                if n.get_id() not in notifications:
                    notifications_map[n.get_id()] = []

                notifications_map[n.get_id()].append(
                    {
                        "cost": listing["cost"],
                        "quantity": listing["quantity"],
                    }
                )

        n: Notification
        for n in notifications:
            if n.get_id() not in notifications_map:
                continue

            fields = []
            i = 1
            total_quantity = 0

            if item.market_value == 0:
                continue

            for listing in notifications_map[n.get_id()]:
                percent_change = round((listing["cost"] - item.market_value) / item.market_value * 100, 1)
                fields.append(
                    {
                        "name": f"Bazaar #{i}",
                        "value": f"{commas(listing['quantity'])}x @ ${commas(listing['cost'])} → ${commas(listing['quantity'] * listing['cost'])} ({percent_change}%)",
                        "inline": True,
                    }
                )
                total_quantity += listing["quantity"]
                i += 1

            send_notification(
                n,
                payload={
                    "embeds": [
                        {
                            "title": f"{item.name} Price Notification",
                            "description": f"{commas(total_quantity)}x of {item.name} have been found in {i - 1} bazaar(s) or market listing(s).",
                            "fields": fields,
                            "color": SKYNET_INFO,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": torn_timestamp()},
                        }
                    ],
                    "components": components,
                },
            )

    if quantity_enabled:
        total_quantity = sum(listing["quantity"] for listing in market_data["bazaar"][:3])

        for n in notifications:
            if n.options["type"] != "quantity" or n.options["value"] < total_quantity:
                continue

            fields = []
            i = 1

            for listing in market_data["bazaar"][:3]:
                percent_change = round((listing["cost"] - item.market_value) / item.market_value * 100, 1)

                fields.append(
                    {
                        "name": f"Bazaar #{i}",
                        "value": f"{commas(listing['quantity'])}x @ ${commas(listing['cost'])} → ${commas(listing['quantity'] * listing['cost'])} ({percent_change}%)",
                        "inline": True,
                    }
                )
                i += 1

            send_notification(
                n,
                payload={
                    "embeds": [
                        {
                            "title": f"{item.name} Quantity Notification",
                            "description": f"{commas(total_quantity)}x of {item.name} have been found in the first "
                            f"three visible bazaars.",
                            "fields": fields,
                            "color": SKYNET_INFO,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": torn_timestamp()},
                        }
                    ],
                    "components": components,
                },
            )

    redis_client.delete(f"tornium:items:{item.tid}:ids")
    market_ids = [listing["ID"] for listing in market_data["itemmarket"] + market_data["bazaar"]]

    if len(market_ids) != 0:
        redis_client.sadd(f"tornium:items:{item.tid}:ids", *market_ids)
