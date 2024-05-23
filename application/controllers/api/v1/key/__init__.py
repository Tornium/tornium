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

import json
import uuid

from flask import request
from peewee import DoesNotExist, IntegrityError
from tornium_celery.tasks.api import tornget
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.models import TornKey

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def set_key(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    api_key = data.get("key")

    if api_key in (None, "") or len(api_key) != 16:
        return make_exception_response("1200", key)

    try:
        key_info = tornget("key/?selections=info", api_key)
        user_info = tornget("user/?selections=basic", api_key)
    except NetworkingError as e:
        return make_exception_response("4100", key, details={"code": e.code, "message": e.message})
    except TornError as e:
        return make_exception_response("4101", key, details={"code": e.code, "message": e.message})

    if key_info["access_level"] == 0:
        return make_exception_response("4002", key)

    try:
        TornKey.insert(
            guid=uuid.uuid4(),
            api_key=api_key,
            user=user_info["player_id"],
            default=False,
            disabled=False,
            paused=False,
            access_level=key_info["access_level"],
        ).execute()
    except IntegrityError as e:
        print(e)
        return make_exception_response("0000", key, details={"message": "Key already exists"})

    return (
        {
            "obfuscated_key": api_key[:6] + "*" * 10,
        },
        200,
        api_ratelimit_response(key),
    )


@session_required
@ratelimit
def toggle_key(guid: str, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    disabled = data.get("disabled")

    if disabled is None or not isinstance(disabled, bool):
        return make_exception_response("0000", key, details={"message": "Invalid disabled state"})

    try:
        key_db = TornKey.select(TornKey.user).where(TornKey.guid == uuid.UUID(guid)).get()
    except DoesNotExist:
        return make_exception_response("1200", key)

    if key_db.user_id != kwargs["user"].tid:
        return make_exception_response("4004", key)

    TornKey.update(disabled=bool(disabled)).where(TornKey.guid == uuid.UUID(guid)).execute()

    try:
        api_key: TornKey = (
            TornKey.select(
                TornKey.api_key,
                TornKey.disabled,
                TornKey.paused,
                TornKey.default,
                TornKey.access_level,
            )
            .where(TornKey.guid == uuid.UUID(guid))
            .get()
        )
    except DoesNotExist:
        return {}, 200, api_ratelimit_response(key)

    return (
        {
            "guid": guid,
            "obfuscated_key": api_key.api_key[:6] + "*" * 10,
            "disabled": api_key.disabled,
            "paused": api_key.paused,
            "default": api_key.default,
            "access_level": api_key.access_level,
        },
        200,
        api_ratelimit_response(key),
    )


@session_required
@ratelimit
def delete_key(guid: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        key_db = TornKey.select().where(TornKey.guid == uuid.UUID(guid)).get()
    except DoesNotExist:
        return make_exception_response("1200", key)

    if key_db.user_id != kwargs["user"].tid:
        return make_exception_response("4004", key)

    key_db.delete_instance()

    return "", 204
