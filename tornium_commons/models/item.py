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
from peewee import (
    BigIntegerField,
    CharField,
    DoesNotExist,
    SmallIntegerField,
    TextField,
    chunked,
)

from ..db_connection import db
from ..redisconnection import rds
from .base_model import BaseModel


class Item(BaseModel):
    tid = SmallIntegerField(primary_key=True)
    name = CharField()
    description = TextField()
    item_type = CharField()
    market_value = BigIntegerField()
    circulation = BigIntegerField()

    @staticmethod
    def update_items(torn_get: typing.Union[typing.Callable, celery.Task], api_key: str):
        """
        Update list of stored Torn items in the database via a Torn API call

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
            endpoint="torn/?selections=items",
            key=api_key,
        )

        bulk_data = []

        # TODO: Combine DB chunked insert and data compilation
        item_id: int
        item: dict
        for item_id, item in items_data["items"].items():
            bulk_data.append(
                {
                    "tid": int(item_id),
                    "name": item.get("name", "").replace('"', "''").replace("'", "''"),
                    "description": item.get("description", "").replace('"', "''").replace("'", "''").replace("%", "%%"),
                    "item_type": item.get("type", ""),
                    "market_value": item.get("market_value", 0),
                    "circulation": item.get("circulation", 0),
                }
            )

        with db().atomic():
            for batch in chunked(bulk_data, 10):
                cmd = """INSERT INTO item (tid, name, description, item_type, market_value, circulation)
                    VALUES
                """

                for data in batch:
                    cmd += f"({data['tid']}, '{data['name']}', '{data['description']}', '{data['item_type']}', {data['market_value']}, {data['circulation']}),\n"

                cmd = cmd[:-2] + "\n"
                cmd += """ON CONFLICT (tid) DO UPDATE
                    SET name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        item_type = EXCLUDED.item_type,
                        market_value = EXCLUDED.market_value,
                        circulation = EXCLUDED.circulation;
                """

                db().execute_sql(cmd)

        redis_client.set(
            "tornium:items:last-update",
            int(datetime.datetime.utcnow().timestamp()),
            ex=5400,
        )  # 1.5 hours

    @staticmethod
    def item_str(tid: int) -> str:
        try:
            _item: Item = Item.select(Item.name).get_by_id(tid)
        except DoesNotExist:
            return f"Unknown {tid}"

        return f"{_item.name} [{tid}]"
