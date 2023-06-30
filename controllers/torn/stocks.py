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
from flask import render_template
from flask_login import current_user, login_required
from tornium_celery.tasks.api import tornget
from tornium_commons import rds
from tornium_commons.models import ItemModel, TickModel


@login_required
def stocks():
    if not current_user.admin:
        return render_template(
            "errors/error.html",
            title="Permission Denied",
            error="This page is still under development. Please check back later.",
        )

    ItemModel.update_items(tornget, current_user.key)

    last_tick: typing.Optional[TickModel] = TickModel.objects().order_by("-_id").first()

    if last_tick is None:
        return render_template(
            "errors/error.html", title="No Stocks Data", error="No stocks data was found in the database."
        )

    stocks_map = rds().json().get("tornium:stocks")

    if stocks_map is None:
        ticks: typing.Union[list, mongoengine.QuerySet] = TickModel.objects(timestamp=last_tick.timestamp)
    else:
        stock_id_list = [int(stock_id) for stock_id in stocks_map.keys()]
        now = int(datetime.datetime.utcnow().replace(second=0, microsecond=0, tzinfo=datetime.timezone.utc).timestamp())
        ticks: typing.Union[list, mongoengine.QuerySet] = [
            TickModel.objects(tick_id=int(bin(stock_id), 2) + int(bin(now << 8), 2)).first()
            for stock_id in stock_id_list
        ]

    return render_template("torn/stocks.html", stocks=ticks)
