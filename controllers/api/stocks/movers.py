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
from mongoengine.queryset.visitor import Q
from tornium_commons import rds
from tornium_commons.models import TickModel

from controllers.api.decorators import authentication_required, ratelimit
from controllers.api.utils import api_ratelimit_response, make_exception_response


def get_closest_tick(stock_id: int, start_timestamp: int):
    for n in range(1, 30):
        tick_id = int(bin(stock_id), 2) + int(bin((start_timestamp + n * 60) << 8), 2)
        tick: typing.Optional[TickModel] = TickModel.objects(tick_id=tick_id).first()

        if tick is not None:
            return tick

    return None


@authentication_required
@ratelimit
def stock_movers(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    redis_client = rds()
    stocks_map = redis_client.json().get("tornium:stocks")

    if stocks_map is None:
        return make_exception_response("1000", key, details={"message": "Cached stocks map could not be located."})

    stock_id_list = [int(stock_id) for stock_id in stocks_map.keys()]

    # movers must use lists to preserve order
    movers_data = {
        "gainers": {
            "d1": [],
            "d7": [],
            "m1": [],
        },
        "losers": {
            "d1": [],
            "d7": [],
            "m1": [],
        },
    }

    now = datetime.datetime.utcnow().replace(second=0, microsecond=0, tzinfo=datetime.timezone.utc)
    timestamp_now = int(now.timestamp())
    d1_start = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
    timestamp_d1_start = int(d1_start.timestamp())
    timestamp_d7_start = int((d1_start - datetime.timedelta(days=6)).timestamp())
    timestamp_m1_start = int((d1_start - datetime.timedelta(days=29)).timestamp())

    current_stock_ticks: typing.Dict[int, typing.Optional[TickModel]] = {
        stock_id: TickModel.objects(tick_id=int(bin(stock_id), 2) + int(bin(timestamp_now << 8), 2)).first()
        for stock_id in stock_id_list
    }

    d1_stock_ticks: typing.Dict[int, typing.Optional[TickModel]] = {
        stock_id: TickModel.objects(tick_id=int(bin(stock_id), 2) + int(bin(timestamp_d1_start << 8), 2)).first()
        for stock_id in stock_id_list
    }
    d7_stock_ticks: typing.Dict[int, typing.Optional[TickModel]] = {
        stock_id: TickModel.objects(tick_id=int(bin(stock_id), 2) + int(bin(timestamp_d7_start << 8), 2)).first()
        for stock_id in stock_id_list
    }
    m1_stock_ticks: typing.Dict[int, typing.Optional[TickModel]] = {
        stock_id: TickModel.objects(tick_id=int(bin(stock_id), 2) + int(bin(timestamp_m1_start << 8), 2)).first()
        for stock_id in stock_id_list
    }

    # Below loops assume that all stocks will not have a value for a timestamp if a single tick does not
    for stock_id, tick in current_stock_ticks.items():
        if tick is None:
            closest_tick = get_closest_tick(stock_id, timestamp_now)

            if closest_tick is None:
                break

            current_stock_ticks[stock_id] = closest_tick

    for stock_id, tick in d1_stock_ticks.items():
        if tick is None:
            closest_tick = get_closest_tick(stock_id, timestamp_d1_start)

            if closest_tick is None:
                break

            d1_stock_ticks[stock_id] = closest_tick

    for stock_id, tick in d7_stock_ticks.items():
        if tick is None:
            closest_tick = get_closest_tick(stock_id, timestamp_d7_start)

            if closest_tick is None:
                break

            d7_stock_ticks[stock_id] = closest_tick

    for stock_id, tick in m1_stock_ticks.items():
        if tick is None:
            closest_tick = get_closest_tick(stock_id, timestamp_m1_start)

            if closest_tick is None:
                break

            m1_stock_ticks[stock_id] = closest_tick

    d1_changes = {}
    d7_changes = {}
    m1_changes = {}

    for stock_id in stock_id_list:
        # dec_change = (new - old) / old

        now_tick: typing.Optional[TickModel] = current_stock_ticks.get(stock_id)

        if now_tick is None:
            continue

        d1_tick: typing.Optional[TickModel] = d1_stock_ticks.get(stock_id)
        d7_tick: typing.Optional[TickModel] = d7_stock_ticks.get(stock_id)
        m1_tick: typing.Optional[TickModel] = m1_stock_ticks.get(stock_id)

        if d1_tick is not None:
            d1_changes[stock_id] = (now_tick.price - d1_tick.price) / d1_tick.price

        if d7_tick is not None:
            d7_changes[stock_id] = (now_tick.price - d7_tick.price) / d7_tick.price

        if m1_tick is not None:
            m1_changes[stock_id] = (now_tick.price - m1_tick.price) / m1_tick.price

    # Changes from low to high
    d1_changes_sorted = sorted(d1_changes, key=d1_changes.get)
    d7_changes_sorted = sorted(d7_changes, key=d7_changes.get)
    m1_changes_sorted = sorted(m1_changes, key=m1_changes.get)

    # [:-6:-1] will reverse the list and return the first five

    # d1 losers
    for stock_id in d1_changes_sorted[:5]:
        movers_data["losers"]["d1"].append(
            {
                "stock_id": stock_id,
                "change": d1_changes[stock_id],
                "price": d1_stock_ticks[stock_id].price,
            }
        )

    # d1 gainers
    for stock_id in d1_changes_sorted[:-6:-1]:
        movers_data["gainers"]["d1"].append(
            {
                "stock_id": stock_id,
                "change": d1_changes[stock_id],
                "price": d1_stock_ticks[stock_id].price,
            }
        )

    # d7 losers
    for stock_id in d7_changes_sorted[:5]:
        movers_data["losers"]["d7"].append(
            {
                "stock_id": stock_id,
                "change": d7_changes[stock_id],
                "price": d7_stock_ticks[stock_id].price,
            }
        )

    # d7 gainers
    for stock_id in d7_changes_sorted[:-6:-1]:
        movers_data["gainers"]["d7"].append(
            {
                "stock_id": stock_id,
                "change": d7_changes[stock_id],
                "price": d7_stock_ticks[stock_id].price,
            }
        )

    # m1 losers
    for stock_id in m1_changes_sorted[:5]:
        movers_data["losers"]["m1"].append(
            {
                "stock_id": stock_id,
                "change": m1_changes[stock_id],
                "price": m1_stock_ticks[stock_id].price,
            }
        )

    # m1 gainers
    for stock_id in m1_changes_sorted[:-6:-1]:
        movers_data["gainers"]["m1"].append(
            {
                "stock_id": stock_id,
                "change": m1_changes[stock_id],
                "price": m1_stock_ticks[stock_id].price,
            }
        )

    return jsonify(movers_data), 200, api_ratelimit_response(key)
