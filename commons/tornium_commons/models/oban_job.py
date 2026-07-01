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

from __future__ import annotations

import datetime
import typing

from peewee import BigAutoField, DateTimeField, IntegerField, TextField
from playhouse.postgres_ext import ArrayField, JSONField

from .base_model import BaseModel


class ObanJob(BaseModel):
    id = BigAutoField()

    # TODO: make `state` an enum
    # See https://github.com/coleifer/peewee/issues/630
    state = TextField()  # public.oban_job_state enum (handled at DB level)
    queue = TextField()
    worker = TextField()

    args = JSONField()
    errors = ArrayField(JSONField)

    attempt = IntegerField()
    max_attempts = IntegerField()

    inserted_at = DateTimeField()
    scheduled_at = DateTimeField()
    attempted_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    attempted_by = ArrayField(TextField, null=True)
    discarded_at = DateTimeField(null=True)
    cancelled_at = DateTimeField(null=True)

    priority = IntegerField()
    tags = ArrayField(TextField, null=True)
    meta = JSONField(null=True)

    class Meta:
        table_name = "oban_job"

    @classmethod
    def new(
        cls,
        worker: str,
        queue: str,
        args: typing.Dict[str, typing.Any],
        state: str = "available",
        max_attempts: int = 5,
        schedule_in: datetime.timedelta = datetime.timedelta(),
        priority: int = 0,
        tags: typing.List[str] = [],
    ) -> ObanJob:
        now = datetime.datetime.utcnow()
        return ObanJob.create(
            state=state,
            queue=queue,
            worker=worker,
            args=args,
            errors=[],
            attempt=0,
            max_attempts=max_attempts,
            inserted_at=now,
            scheduled_at=now + schedule_in,
            attempted_at=None,
            completed_at=None,
            attempted_by=None,
            discarded_at=None,
            cancelled_at=None,
            priority=priority,
            tags=tags + ["python-invoked"],
            meta={},
        )
