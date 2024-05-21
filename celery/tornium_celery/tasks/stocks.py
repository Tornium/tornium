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
import time
import typing

import celery
from celery.utils.log import get_task_logger
from redis.commands.json.path import Path
from tornium_commons import rds
from tornium_commons.formatters import commas, timestamp, torn_timestamp
from tornium_commons.models import Notification, StockTick, TornKey
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO

from .api import discordpost, tornget
from .misc import send_dm

logger = get_task_logger("celery_app")


def _map_stock_image(acronym: str):
    return f"https://www.torn.com/images/v2/stock-market/portfolio/{acronym.upper()}.png"


def _get_stocks_tick(
    stock_id: int, stocks_timestamp: typing.Optional[datetime.datetime] = None, **kwargs
) -> typing.Optional[StockTick]:
    minutes_ago = kwargs.get("minutes", 0)
    hours_ago = kwargs.get("hours", 0)
    days_ago = kwargs.get("days", 0)
    binary_stock_id = bin(stock_id)

    if stocks_timestamp is None:
        stocks_timestamp = datetime.datetime.utcnow()

    stocks_timestamp = stocks_timestamp - datetime.timedelta(minutes=minutes_ago, hours=hours_ago, days=days_ago)

    return (
        StockTick.select()
        .where(StockTick.tick_id == int(binary_stock_id, 2) + int(bin(int(timestamp(stocks_timestamp)) << 8), 2))
        .first()
    )


@celery.shared_task(
    name="tasks.stocks.stocks_prefetch",
    routing_key="quick.stocks_prefetch",
    queue="quick",
    time_limit=5,
)
def stocks_prefetch():
    stocks_timestamp = datetime.datetime.utcnow().replace(second=5, microsecond=0, tzinfo=datetime.timezone.utc)

    if int(time.time()) % 60 >= 5:
        kwargs = {}
    else:
        kwargs = {"eta": stocks_timestamp}

    return tornget.signature(
        kwargs={
            "endpoint": "torn/?selections=stocks",
            "key": TornKey.random_key().api_key,
        },
        queue="api",
    ).apply_async(
        expires=50,
        link=celery.chain(
            update_stock_prices.signature(kwargs={"stocks_timestamp": stocks_timestamp}),
            celery.group(
                stock_price_notifications.s(),
                stock_notifications.signature(
                    kwargs={
                        "stocks_timestamp": stocks_timestamp,
                    }
                ),
            ),
        ),
        **kwargs,
    )


@celery.shared_task(
    name="tasks.stocks.update_stock_prices",
    routing_key="quick.update_stock_prices",
    queue="quick",
    time_limit=5,
)
def update_stock_prices(stocks_data, stocks_timestamp: datetime.datetime = datetime.datetime.utcnow()):
    if stocks_data is None:
        raise ValueError

    stocks_timestamp = stocks_timestamp.replace(second=0, tzinfo=datetime.timezone.utc)
    binary_timestamp = bin(int(timestamp(stocks_timestamp)) << 8)

    stocks = {stock["stock_id"]: stock["acronym"] for stock in stocks_data["stocks"].values()}
    stock_benefits = {stock["stock_id"]: stock["benefit"] for stock in stocks_data["stocks"].values()}
    stocks_insert_data = [
        {
            "tick_id": int(bin(stock["stock_id"]), 2) + int(binary_timestamp, 2),
            "timestamp": stocks_timestamp,
            "stock_id": stock["stock_id"],
            "price": stock["current_price"],
            "cap": stock["market_cap"],
            "shares": stock["total_shares"],
            "investors": stock["investors"],
        }
        for stock in stocks_data["stocks"].values()
    ]

    StockTick.insert_many(stocks_insert_data).execute()

    rds().json().set("tornium:stocks", Path.root_path(), stocks)
    rds().json().set("tornium:stocks:benefits", Path.root_path(), stock_benefits)

    return stocks_data


@celery.shared_task(
    name="tasks.stocks.stock_price_notifications",
    routing_key="default.stock_price_notifications",
    queue="default",
    time_limit=5,
)
def stock_price_notifications(stocks_data: dict):
    notification: Notification
    for notification in Notification.select().where(Notification.n_type == 0):
        target_stock = stocks_data["stocks"][str(notification.target)]

        stock_timestamp = int(timestamp(notification.time_created) // 60 * 60)
        stock_tick: typing.Optional[StockTick] = (
            StockTick.select(StockTick.price)
            .where(StockTick.tick_id == int(bin(target_stock["stock_id"]), 2) + int(bin(stock_timestamp << 8), 2))
            .first()
        )

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
                            "value": (
                                f"${commas(stock_tick.price, stock_price=True)}"
                                if stock_tick is not None
                                else "Unknown"
                            ),
                            "inline": True,
                        },
                        {
                            "name": "Target Price",
                            "value": f"${commas(notification.options['value'], stock_price=True)}",
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

        if (
            notification.options.get("equality") == ">"
            and target_stock["current_price"] > notification.options["value"]
        ):
            payload["embeds"][0]["title"] = "Above Target Price"
            payload["embeds"][0]["color"] = SKYNET_GOOD
        elif (
            notification.options.get("equality") == "<"
            and target_stock["current_price"] < notification.options["value"]
        ):
            payload["embeds"][0]["title"] = "Below Target Price"
            payload["embeds"][0]["color"] = SKYNET_ERROR
        elif (
            notification.options.get("equality") == "="
            and target_stock["current_price"] == notification.options["value"]
        ):
            payload["embeds"][0]["title"] = "Reached Target Price"
            payload["embeds"][0]["color"] = SKYNET_GOOD
        else:
            continue

        if notification.recipient_guild == 0:
            send_dm.delay(notification.recipient, payload=payload).forget()
        else:
            discordpost.delay(f"channels/{notification.recipient}/messages", payload=payload).forget()

        if not notification.persistent:
            notification.delete_instance()


@celery.shared_task(
    name="tasks.stocks.stock_notifications",
    routing_key="default.stock_notifications",
    queue="default",
    time_limit=5,
)
def stock_notifications(stocks_data: dict, stocks_timestamp: datetime.datetime = datetime.datetime.utcnow()):
    return  # TODO: Rewrite

    def base_embed(target_stock: dict) -> dict:
        return {
            "author": {
                "name": target_stock["name"],
            },
            "image": {
                "url": _map_stock_image(target_stock["acronym"]),
            },
            "fields": [],
            "footer": {"text": torn_timestamp()},
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }

    redis_client = rds()

    # Percent change
    # Periods: 1h, 4h, 12h, 24h, 7d

    # Market cap change
    # Only 1m period
    cap_change_channels: typing.Optional[list] = None

    stock: dict
    for stock in stocks_data["stocks"].values():
        stock_id = stock["stock_id"]
        minute_tick: typing.Optional[TickModel] = _get_stocks_tick(stock_id, minutes=1)

        if minute_tick is None:
            continue
        elif abs(stock["market_cap"] - minute_tick.cap) > 150_000_000_000:
            continue

        embed = base_embed(stock)

        if minute_tick.cap > stock["market_cap"]:
            embed["title"] = f"High Market Demand: {stock['name']}"
            embed["color"] = SKYNET_ERROR
        else:
            embed["title"] = f"High Market Selloff: {stock['name']}"
            embed["color"] = SKYNET_GOOD

        embed["fields"].append(
            {
                "name": "Market Cap",
                "value": f"${commas(stock['market_cap'])}",
            }
        )
        embed["fields"].append(
            {
                "name": "Price",
                "value": f"${commas(stock['current_price'], stock_price=True)}",
            }
        )
        embed["fields"].append(
            {
                "name": "Cap Change",
                "value": f"${commas(abs(stock['market_cap'] - minute_tick.cap))} ({round(abs(stock['market_cap'] - minute_tick.cap)/minute_tick.cap, 2)}%)",
            }
        )

        if cap_change_channels is None:
            cap_change_channels = []

            guild: ServerModel
            for guild in ServerModel.objects(Q(stocks_config__cap_change=True) & Q(stocks_channel__nin=[0, None])):
                cap_change_channels.append(guild.stocks_channel)

        for channel in cap_change_channels:
            discordpost.delay(f"channels/{channel}/messages", payload=embed).forget()

    embeds = []
    # New day price
    # Once a day at 00:00
    if stocks_timestamp.hour == 0 and stocks_timestamp.minute == 0:
        stock: dict
        for stock in stocks_data["stocks"].values():
            previous_opening_ts = (
                int(stocks_timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()) - 86400
            )  # One day ago
            previous_opening_tick: typing.Optional[TickModel] = (
                TickModel.objects(tick_id=int(bin(stock["stock_id"]), 2) + int(bin(previous_opening_ts << 8), 2))
                .only("price")
                .first()
            )

            if previous_opening_tick is None:
                continue

            embed = base_embed(stock)
            embed["title"] = f"New Day: {stock['name']}"
            embed["fields"].append(
                {
                    "name": "New Day Opening Price",
                    "value": f"${commas(stock['current_price'], stock_price=True)}",
                    "inline": True,
                }
            )
            embed["fields"].append(
                {
                    "name": "Yesterday's Opening Price",
                    "value": f"${commas(previous_opening_tick.price, stock_price=True)}",
                    "inline": True,
                }
            )
            embed["fields"].append(
                {
                    "name": "Day to Day Price Change (%)",
                    "value": f"{round((stock['current_price'] - previous_opening_tick.price) / previous_opening_tick.price * 100, 2)}",
                }
            )
            embed["fields"].append(
                {
                    "name": "Market Cap",
                    "value": commas(stock["market_cap"]),
                }
            )
            embed["color"]: SKYNET_INFO
            embeds.append(embed)

        guild: ServerModel
        for guild in ServerModel.objects(Q(stocks_config__new_day_price=True) & Q(stocks_channel__nin=[0, None])):
            # TODO: Verify formatting of multiple embeds in one message
            # TOOO: Split into multiple messages if necessary

            discordpost.delay(f"channels/{guild.stocks_channel}/messages", payload=embeds).forget()

    # Minimum price & Maximum price
    # Within 1% of minimum/maxmimum price during period
    # Periods: 7d, 14d, 1m

    # min_price_channels: typing.Optional[list] = None
    # max_price_channels: typing.Optional[list] = None

    stock: dict
    for stock in stocks_data["stocks"].values():
        stock_id = stock["stock_id"]

        price_min = redis_client.get(f"tornium:stocks:{stock_id}:min")
        price_max = redis_client.get(f"tornium:stocks:{stock_id}:max")

        seven_ticks: typing.Optional[QuerySet] = None
        fourteen_ticks: typing.Optional[QuerySet] = None
        month_ticks: typing.Optional[QuerySet] = None

        if price_min is None:
            seven_ticks = TickModel.objects(
                timestamp__gte=int((datetime.datetime.utcnow() - datetime.timedelta(days=7)).timestamp())
            ).only("price")
            fourteen_ticks = TickModel.objects(
                timestamp__gte=int((datetime.datetime.utcnow() - datetime.timedelta(days=14)).timestamp())
            ).only("price")
            month_ticks = TickModel.objects(
                timestamp__gte=int((datetime.datetime.utcnow() - datetime.timedelta(days=30)).timestamp())
            ).only("price")

            seven_min = seven_ticks.order_by("price").first().price
            fourteen_min = fourteen_ticks.order_by("price").first().price
            month_min = month_ticks.order_by("price").first().price

            redis_client.set(
                f"tornium:stocks:{stock_id}:min",
                f"{seven_min}|{fourteen_min}|{month_min}",
                ex=3600,
            )
        else:
            seven_min, fourteen_min, month_min = [float(n) for n in price_min.split("|")]

            if seven_min * 1.01 > stock["current_price"]:
                embed = base_embed(stock)
                embed["title"] = f"7-Day Low: {stock['name']}"
                embed["description"] = (
                    f"{stock['name']} is within 1% of the 7 day low (${commas(seven_min, stock_price=True)})."
                )
                embed["color"] = SKYNET_ERROR

                embed["fields"].append(
                    {
                        "name": "Market Cap",
                        "value": f"${commas(stock['market_cap'])}",
                    }
                )
                embed["fields"].append(
                    {
                        "name": "Price",
                        "value": f"${commas(stock['current_price'], stock_price=True)}",
                    }
                )

                guild: ServerModel
                for guild in ServerModel.objects(Q(stocks_config__min_price=True) & Q(stocks_channel__nin=[0, None])):
                    pass

            if fourteen_min * 1.01 > stock["current_price"]:
                embed = base_embed(stock)
                embed["title"] = f"14-Day Low: {stock['name']}"
                embed["description"] = (
                    f"{stock['name']} is within 1% of the 14 day low (${commas(fourteen_min, stock_price=True)})."
                )
                embed["color"] = SKYNET_ERROR

                embed["fields"].append(
                    {
                        "name": "Market Cap",
                        "value": f"${commas(stock['market_cap'])}",
                    }
                )
                embed["fields"].append(
                    {
                        "name": "Price",
                        "value": f"${commas(stock['current_price'], stock_price=True)}",
                    }
                )

            if month_min * 1.01 > stock["current_price"]:
                embed = base_embed(stock)
                embed["title"] = f"1-Month Low: {stock['name']}"
                embed["description"] = (
                    f"{stock['name']} is within 1% of the 1 month low (${commas(seven_min, stock_price=True)})."
                )
                embed["color"] = SKYNET_ERROR

                embed["fields"].append(
                    {
                        "name": "Market Cap",
                        "value": f"${commas(stock['market_cap'])}",
                    }
                )
                embed["fields"].append(
                    {
                        "name": "Price",
                        "value": f"${commas(stock['current_price'], stock_price=True)}",
                    }
                )

        if price_max is None:
            if seven_ticks is None:
                seven_ticks = TickModel.objects(
                    timestamp__gte=int((datetime.datetime.utcnow() - datetime.timedelta(days=7)).timestamp())
                ).only("price")
                fourteen_ticks = TickModel.objects(
                    timestamp__gte=int((datetime.datetime.utcnow() - datetime.timedelta(days=14)).timestamp())
                ).only("price")
                month_ticks = TickModel.objects(
                    timestamp__gte=int((datetime.datetime.utcnow() - datetime.timedelta(days=30)).timestamp())
                ).only("price")

                seven_max = seven_ticks.order_by("-price").first().price
                fourteen_max = fourteen_ticks.order_by("-price").first().price
                month_max = month_ticks.order_by("-price").first().price

                redis_client.set(
                    f"tornium:stocks:{stock_id}:max",
                    f"{seven_max}|{fourteen_max}|{month_max}",
                    ex=3600,
                )
        else:
            seven_max, fourteen_max, month_max = [float(n) for n in price_max.split("|")]

            if seven_max * 1.01 < stock["current_price"]:
                pass

            if fourteen_max * 1.01 < stock["current_price"]:
                pass

            if month_max * 1.01 < stock["current_price"]:
                pass
