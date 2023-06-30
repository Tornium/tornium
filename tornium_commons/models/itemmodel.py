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

import celery
from mongoengine import DynamicDocument, IntField, StringField
from pymongo import UpdateOne

from .. import rds


class ItemModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField(default="")
    description = StringField(default="")
    type = StringField(default="")
    market_value = IntField(default=0)
    circulation = IntField(default=0)

    @staticmethod
    def update_items(torn_get: typing.Union[typing.Callable, celery.Task], api_key: str):
        """
        Update list of stored Torn items in teh database via a Torn API call

        Parameters
        ----------
        torn_get : Callable, celery.Task
            Celery task or function calling the Torn API (e.g. `tornium_celery.tasks.tornget`)
        api_key : str
            Torn API key used for the Torn API call

        Returns
        -------
        None

        Raises
        ------
        MissingKeyError
            No API key passed
        requests.exceptions.Timeout
            API called timed out
        NetworkingError
            HTTP error code
        TornError
            Torn error code
        """

        redis_client = rds()
        last_update = redis_client.get("tornium:items:last-update")

        if last_update is not None and (  # Redis value exists for last update
            # Updated less than an hour ago
            int(datetime.datetime.utcnow().timestamp()) - int(last_update) <= 3600
            # Last update was a different day
            or datetime.datetime.fromtimestamp(int(last_update)).day != datetime.datetime.utcnow().day
        ):
            return

        items_data = torn_get(
            endpoint=f"torn/?selections=items",
            key=api_key,
        )
        bulk_operations = []

        item_id: int
        item: dict
        for item_id, item in items_data["items"].items():
            bulk_operations.append(
                UpdateOne(
                    {"tid": item_id},
                    {
                        "$set": {
                            "tid": item_id,
                            "name": item.get("name", ""),
                            "description": item.get("description", ""),
                            "type": item.get("type", ""),
                            "market_value": item.get("market_value", 0),
                            "circulation": item.get("circulation", 0),
                        }
                    },
                    upsert=True,
                )
            )

        ItemModel._get_collection().bulk_write(bulk_operations, ordered=False)
        redis_client.set("tornium:items:last-update", int(datetime.datetime.utcnow().timestamp()), ex=5400)  # 1.5 hours
