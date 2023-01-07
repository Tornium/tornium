# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import random
import time

from redis.commands.json.path import Path

import skynet.skyutils
from models.notificationmodel import NotificationModel
from models.tickmodel import TickModel
from models.usermodel import UserModel
import redisdb
from tasks import celery_app, logger, tornget, discordpost
import utils


def _map_stock_image(acronym: str):
    return f"https://www.torn.com/images/v2/stock-market/portfolio/{acronym.upper()}.png"


@celery_app.task
def fetch_stock_ticks():
    time.sleep(5)  # Torn has stock tick data ready at xx:xx:05

    auth_users = [user.key for user in UserModel.objects(key__nin=[None, ""])]
    random.shuffle(auth_users)

    stocks_data = None
    torn_key = random.choice(auth_users)
    timeout_retry = False

    while stocks_data is None:
        try:
            stocks_data = tornget("torn/?selections=stocks", key=torn_key, nocache=True)
        except utils.TornError as e:
            if e.code in (1, 2, 3, 4, 6, 7, 8, 9):
                return

            torn_key = random.choice(auth_users)
        except utils.NetworkingError as e:
            if e.code == 408 and not timeout_retry:
                timeout_retry = True
                continue

            torn_key = random.choice(auth_users)
            timeout_retry = False

    if stocks_data is None:
        return

    tick_data = []
    now = datetime.datetime.utcnow()
    now = int(
        datetime.datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            second=0,
        )
        .replace(tzinfo=datetime.timezone.utc)
        .timestamp()
    )
    binary_timestamp = bin(now << 8)

    stocks = {}

    for stock in stocks_data["stocks"].values():
        binary_stockid = bin(stock["stock_id"])

        tick_data.append(
            {
                "tick_id": int(binary_stockid, 2) + int(binary_timestamp, 2),
                "timestamp": now,
                "stock_id": stock["stock_id"],
                "price": stock["current_price"],
                "cap": stock["market_cap"],
                "shares": stock["total_shares"],
                "investors": stock["investors"],
            }
        )

        stocks[stock["stock_id"]] = stock["acronym"]

    redisdb.get_redis().json().set("tornium:stocks", Path.root_path(), stocks)

    tick_data = [TickModel(**tick) for tick in tick_data]
    TickModel.objects.insert(tick_data)

    notification: NotificationModel
    for notification in NotificationModel.objects(ntype=0):
        target_stock = stocks_data["stocks"][str(notification.target)]

        stock_timestamp = notification.time_created // 60 * 60
        stock_tick: TickModel = TickModel.objects(
            tick_id=int(bin(target_stock["stock_id"]), 2) + int(bin(stock_timestamp << 8), 2)
        ).first()

        payload = {
            "embeds": [
                {
                    "author": {
                        "name": target_stock["name"],
                    },
                    "image": {
                        "url": _map_stock_image(target_stock["acronym"]),
                    },
                    "fields": [
                        {
                            "name": "Original Price",
                            "value": f"${stock_tick.price}" if stock_tick is not None else "Unknown",
                            "inline": True,
                        },
                        {
                            "name": "Current Price",
                            "value": f"${target_stock['current_price']}",
                            "inline": True,
                        },
                    ],
                    "footer": {"text": utils.torn_timestamp()},
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }

        if notification.options.get("equality") == ">" and target_stock["current_price"] > notification.target:
            payload["embeds"][0]["title"] = "Above Target Price"
            payload["embeds"][0]["color"] = skynet.skyutils.SKYNET_GOOD
        elif notification.options.get("equality") == "<" and target_stock["current_price"] < notification.target:
            payload["embeds"][0]["title"] = "Below Target Price"
            payload["embeds"][0]["color"] = skynet.skyutils.SKYNET_ERROR
        else:
            payload["embeds"][0]["title"] = "Reached Target Price"
            payload["embeds"][0]["color"] = skynet.skyutils.SKYNET_GOOD

        if payload is None:
            continue

        if notification.recipient_type == 0:
            try:
                dm_channel = discordpost(
                    "users/@me/channel",
                    payload={
                        "recipient_id": notification.recipient,
                    },
                )
            except utils.DiscordError:
                continue
            except utils.NetworkingError:
                continue

            discordpost.delay(f"channels/{dm_channel['id']}/messages", payload=payload)
        elif notification.recipient_type == 1:
            discordpost.delay(f"channels/{notification.recipient}/messages", payload=payload)
        else:
            return
