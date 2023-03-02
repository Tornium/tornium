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
import time

import celery
import logging
from pymongo.errors import BulkWriteError
from redis.commands.json.path import Path

from tornium_commons import rds
from tornium_commons.errors import DiscordError, NetworkingError, TornError
from tornium_commons.formatters import commas, torn_timestamp
from tornium_commons.models import NotificationModel, TickModel, UserModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from tornium_celery.tasks.api import tornget, discordpost


def _map_stock_image(acronym: str):
    return f"https://www.torn.com/images/v2/stock-market/portfolio/{acronym.upper()}.png"


@celery.shared_task
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
        except TornError as e:
            if e.code in (1, 2, 3, 4, 6, 7, 8, 9):
                return

            torn_key = random.choice(auth_users)
        except NetworkingError as e:
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

    rds().json().set("tornium:stocks", Path.root_path(), stocks)

    # Resolves duplicate keys: https://github.com/MongoEngine/mongoengine/issues/1465#issuecomment-445443894
    try:
        tick_data = [TickModel(**tick).to_mongo() for tick in tick_data]
        TickModel._get_collection().insert_many(tick_data, ordered=False)
    except BulkWriteError:
        logging.getLogger("celery").warning(
            "Stock tick data bulk insert failed. Duplicates may have been found and were skipped."
        )
    except Exception as e:
        logging.getLogger("celery").exception(e)

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
                            "value": f"${commas(stock_tick.price, stock_price=True)}"
                            if stock_tick is not None
                            else "Unknown",
                            "inline": True,
                        },
                        {
                            "name": "Target Price",
                            "value": f"${commas(notification.value, stock_price=True)}",
                            "inline": True,
                        },
                        {
                            "name": "Current Price",
                            "value": f"${commas(target_stock['current_price'], stock_price=True)}",
                            "inline": True,
                        },
                    ],
                    "footer": {"text": torn_timestamp()},
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }

        if notification.options.get("equality") == ">" and target_stock["current_price"] > notification.value:
            payload["embeds"][0]["title"] = "Above Target Price"
            payload["embeds"][0]["color"] = SKYNET_GOOD
        elif notification.options.get("equality") == "<" and target_stock["current_price"] < notification.value:
            payload["embeds"][0]["title"] = "Below Target Price"
            payload["embeds"][0]["color"] = SKYNET_ERROR
        elif notification.options.get("equality") == "=" and target_stock["current_price"] == notification.value:
            payload["embeds"][0]["title"] = "Reached Target Price"
            payload["embeds"][0]["color"] = SKYNET_GOOD
        else:
            continue

        if payload is None:
            continue

        if notification.recipient_type == 0:
            try:
                dm_channel = discordpost(
                    "users/@me/channels",
                    payload={
                        "recipient_id": notification.recipient,
                    },
                )
            except DiscordError:
                continue
            except NetworkingError:
                continue

            discordpost.delay(f"channels/{dm_channel['id']}/messages", payload=payload)
        elif notification.recipient_type == 1:
            discordpost.delay(f"channels/{notification.recipient}/messages", payload=payload)
        else:
            continue

        if not notification.persistent:
            notification.delete()
