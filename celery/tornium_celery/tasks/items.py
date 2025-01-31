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

from tornium_commons import rds
from tornium_commons.models import Item, User

import celery
from celery.utils.log import get_task_logger

from .api import tornget

logger = get_task_logger("celery_app")


@celery.shared_task(
    name="tasks.items.update_items",
    routing_key="default.items.update_items",
    queue="default",
    time_limit=15,
)
def update_items(items_data):
    Item.update_items(torn_get=tornget, key=User.random_key().api_key)

    rds().set(
        "tornium:items:last-update",
        int(datetime.datetime.utcnow().timestamp()),
        ex=5400,
    )  # 1.5 hours
