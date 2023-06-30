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

import mongoengine
from flask import jsonify
from tornium_commons import rds
from tornium_commons.models import TickModel

from controllers.api.decorators import authentication_required, ratelimit
from controllers.api.utils import api_ratelimit_response, make_exception_response


@authentication_required
@ratelimit
def stocks_data(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    stocks_map = rds().json().get("tornium:stocks")

    if stocks_map is None:
        last_tick: typing.Optional[TickModel] = TickModel.objects().order_by("-_id").first()

        if last_tick is None:
            return make_exception_response("1000", key, details={"message": "Failed to located last stocks tick."})

        ticks: typing.Union[list, mongoengine.QuerySet] = TickModel.objects(timestamp=last_tick.timestamp)
    else:
        stock_id_list = [int(stock_id) for stock_id in stocks_map.keys()]
        now = datetime.datetime.utcnow()

        if now.second <= 6:
            # If time is in next minute but before stocks tick update has occurred
            now = now - datetime.timedelta(minutes=1)

        now = int(now.replace(second=0, microsecond=0, tzinfo=datetime.timezone.utc).timestamp())
        ticks: typing.Union[list, mongoengine.QuerySet] = [
            TickModel.objects(tick_id=int(bin(stock_id), 2) + int(bin(now << 8), 2)).first()
            for stock_id in stock_id_list
        ]

    stocks_tick_data = {}

    tick: typing.Optional[TickModel]
    for tick in ticks:
        if tick is None:
            return make_exception_response("1000", key, details={"message": "Unknown stocks tick."})

        stocks_tick_data[tick.stock_id] = {
            "timestamp": tick.timestamp,
            "price": tick.price,
            "market_cap": tick.cap,
            "shares": tick.shares,
            "investors": tick.investors,
            "acronym": None if stocks_map is None else stocks_map.get(str(tick.stock_id)),
        }

    return jsonify(stocks_tick_data), 200, api_ratelimit_response(key)
