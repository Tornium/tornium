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

from flask import jsonify
from peewee import DoesNotExist
from redis.commands.json.path import Path
from tornium_celery.tasks.api import tornget
from tornium_commons import rds
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.formatters import parse_item_str
from tornium_commons.models import Item, StockTick

from controllers.api.decorators import authentication_required, global_cache, ratelimit
from controllers.api.utils import api_ratelimit_response, make_exception_response


@authentication_required
@ratelimit
@global_cache
def stocks_data(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    stocks_map = rds().json().get("tornium:stocks")

    if stocks_map is None:
        try:
            last_tick: StockTick = StockTick.select(StockTick.timestamp).order_by(-StockTick.tick_id).get()
        except DoesNotExist:
            return make_exception_response("1000", key, details={"message": "Failed to located last stocks tick."})

        ticks: typing.Iterable[StockTick] = StockTick.select().where(StockTick.timestamp == last_tick.timestamp)
    else:
        stock_id_list = [int(stock_id) for stock_id in stocks_map.keys()]
        now = datetime.datetime.utcnow()

        if now.second <= 6:
            # If time is in next minute but before stocks tick update has occurred
            now = now - datetime.timedelta(minutes=1)

        now = int(now.replace(second=0, microsecond=0, tzinfo=datetime.timezone.utc).timestamp())

        ticks: typing.List[StockTick] = []

        for stock_id in stock_id_list:
            try:
                ticks[stock_id] = StockTick.get_by_id(int(bin(stock_id), 2) + int(bin(now << 8), 2))
            except DoesNotExist:
                return make_exception_response("1000", key, details={"message": "Unknown stocks tick."})

    stocks_tick_data = {}

    tick: StockTick
    for tick in ticks:
        stocks_tick_data[tick.stock_id] = {
            "timestamp": tick.timestamp.timestamp(),
            "price": tick.price,
            "market_cap": tick.cap,
            "shares": tick.shares,
            "investors": tick.investors,
            "acronym": None if stocks_map is None else stocks_map.get(str(tick.stock_id)),
        }

    return jsonify(stocks_tick_data), 200, api_ratelimit_response(key)


@authentication_required
@ratelimit
@global_cache(duration=86400)
def stock_benefits(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    stock_benefits_data: dict = rds().json().get("tornium:stocks:benefits")

    if stock_benefits_data is None:
        stock_benefits_data = {}

        try:
            stocks_api_data = tornget("torn/?selections=stocks,stats", kwargs["user"].key)
        except NetworkingError:
            return make_exception_response("4100", key)
        except TornError:
            return make_exception_response("4101", key)

        for stock in stocks_api_data["stocks"].values():
            stock_benefits_data[stock["stock_id"]] = stock["benefit"]

        rds().json().set("tornium:stocks:benefits", Path.root_path(), stock_benefits_data)
        rds().set(
            "tornium:points-value",
            stocks_api_data["stats"]["points_averagecost"],
            ex=86400,
        )

    Item.update_items(tornget, kwargs["user"].key)
    stock_benefits_json = {"active": [], "non_rev": [], "passive": []}

    for stock_id, benefit in stock_benefits_data.items():
        if benefit["type"] == "passive":
            stock_benefits_json["passive"].append(
                {
                    "stock_id": stock_id,
                    "benefit": {
                        "requirement": benefit["requirement"],
                        "frequency": None,
                        "description": benefit["description"],
                        "item": None,
                        "value": None,
                    },
                }
            )
        else:
            if benefit["description"].startswith("$"):
                stock_benefits_json["active"].append(
                    {
                        "stock_id": stock_id,
                        "benefit": {
                            "requirement": benefit["requirement"],
                            "frequency": benefit["frequency"],
                            "description": benefit["description"],
                            "item": None,
                            "value": int("".join(benefit["description"][1:].split(","))),
                        },
                    }
                )
                continue

            quantity: int
            item: typing.Optional[Item]
            quantity, item = parse_item_str(benefit["description"])

            if item is None:
                if "Random Property" in benefit["description"]:
                    value = 45_456_057.69  # Based on NPC sell price (75% of buy price)
                elif "Clothing Cache" in benefit["description"]:
                    _clothing_caches = [
                        "Gentleman Cache",
                        "Elegant Cache",
                        "Naughty Cache",
                        "Elderly Cache",
                        "Denim Cache",
                        "Wannabe Cache",
                        "Cutesy Cache",
                        "Injury Cache",
                    ]
                    clothing_cache_values = []

                    for name in _clothing_caches:
                        try:
                            item = Item.get(Item.name == name)
                        except DoesNotExist:
                            return make_exception_response("1104", key, details={"item": name})

                        if item.market_value <= 0:
                            continue

                        clothing_cache_values.append(item.market_value)

                    value = round(sum(clothing_cache_values) / len(clothing_cache_values), 2)
                elif "points" in benefit["description"]:
                    points_value = rds().get("tornium:points-value")
                    if points_value is None:
                        try:
                            stats_data = tornget("torn/?selections=stats", kwargs["user"].key)
                        except (NetworkingError, TornError):
                            continue

                        points_value = stats_data["stats"]["points_averagecost"]
                        rds().set("tornium:points-value", points_value, ex=86400)

                    try:
                        # Uses "100 Points" instead of "100x Points"
                        value = 100 * int(points_value)
                    except TypeError:
                        continue
                else:
                    value = None

                benefit_data = {
                    "stock_id": stock_id,
                    "benefit": {
                        "requirement": benefit["requirement"],
                        "frequency": benefit["frequency"],
                        "description": benefit["description"],
                        "item": None,
                        "value": value,
                    },
                }

                if value is None:
                    stock_benefits_json["non_rev"].append(benefit_data)
                else:
                    stock_benefits_json["active"].append(benefit_data)
            else:
                stock_benefits_json["active"].append(
                    {
                        "stock_id": stock_id,
                        "benefit": {
                            "requirement": benefit["requirement"],
                            "frequency": benefit["frequency"],
                            "description": benefit["description"],
                            "item": {
                                "tid": item.tid,
                                "name": item.name,
                                "description": item.description,
                            },
                            "value": item.market_value,
                        },
                    }
                )

    return jsonify(stock_benefits_json), 200, api_ratelimit_response(key)
