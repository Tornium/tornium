# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import typing

from peewee import BigAutoField, DateTimeField, IntegerField, TextField
from playhouse.postgres_ext import ArrayField, BinaryJSONField

from .models.base_model import BaseModel


class ObanJob(BaseModel):
    """
    A Python migration to Oban from Celery

    See https://hexdocs.pm/oban/migrating-from-other-languages.html for more information.
    """

    class Meta:
        table_name = "oban_jobs"

    id = BigAutoField(primary_key=True)
    # TODO: Add an enum for the choices of state
    state = TextField(choices=[], null=False)
    queue = TextField(null=False)
    worker = TextField(null=False)
    args = BinaryJSONField(default={}, null=False)
    errors = ArrayField(BinaryJSONField, default=[], null=False)
    attempt = IntegerField(null=False)
    max_attempts = IntegerField(null=False)
    inserted_at = DateTimeField(null=False)
    scheduled_at = DateTimeField(null=False)
    attempted_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    attempted_by = ArrayField(TextField, null=True, default=None)
    discarded_at = DateTimeField(null=True)
    priority = IntegerField(default=0)
    tags = ArrayField(TextField, default=list)
    meta = BinaryJSONField(default=dict)
    cancelled_at = DateTimeField(null=True)

    @staticmethod
    def insert(
        worker: str,
        queue: str,
        args: dict = {},
        priority: int = 0,
        scheduled_at: typing.Optional[datetime.datetime] = None,
    ):
        """
        Insert an Oban job by the worker name and the queue name.
        """
        # TODO: Add tests for this
        return ObanJob.create(
            worker=worker,
            queue=queue,
            args=args,
            priority=priority,
            scheduled_at=scheduled_at or datetime.datetime.utc_now(),
            state="scheduled" if scheduled_at else "available",
        )
