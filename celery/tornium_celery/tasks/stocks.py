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

from redis.commands.json.path import Path
from tornium_commons import rds
from tornium_commons.formatters import commas, timestamp, torn_timestamp
from tornium_commons.models import StockTick, TornKey
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

import celery
from celery.utils.log import get_task_logger

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
        link=update_stock_prices.signature(kwargs={"stocks_timestamp": stocks_timestamp}),
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
