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

import inspect
import json
import time
import uuid

from flask import request
from peewee import DoesNotExist, IntegrityError
from tornium_celery.tasks.api import tornget
from tornium_celery.tasks.misc import send_dm
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.models import AuthAction, TornKey
from tornium_commons.skyutils import SKYNET_WARNING

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response
from controllers.authroutes import _log_auth


def send_security_alert(api_user_discord_id: int, api_user_id: int, invoker_user_id: int) -> None:
    if api_user_discord_id in (0, None, ""):
        return

    discord_payload = {
        "embeds": [
            {
                "title": "Security Alert",
                "description": inspect.cleandoc(
                    f"""Someone has attempted to add an API key belonging to your Torn account (ID {api_user_id}) to their Tornium account (ID {api_user_id}) from {request.headers.get("CF-Connecting-IP") or request.remote_addr} [{request.headers.get("CF-IPCountry")}] <t:{int(time.time())}:R>.

                    If this was not intended, please contact the developer as soon as possible. You may need to reset your API key to secure your account and API key."""
                ),
                "color": SKYNET_WARNING,
            }
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": "tiksan [2383326] @ Torn (preferred)",
                        "url": "https://www.torn.com/profiles.php?XID=2383326",
                    },
                ],
            },
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": "tiksan [2383326] @ Discord",
                        "url": "https://discord.com/users/695828257949352028",
                    }
                ],
            },
        ],
    }

    send_dm.delay(api_user_discord_id, discord_payload).forget()


@session_required
@ratelimit
def set_key(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    api_key = data.get("key")

    if api_key in (None, "") or not isinstance(api_key, str) or len(api_key) != 16:
        _log_auth(kwargs["user"].tid, AuthAction.API_KEY_ADD_FAILED, api_key)
        return make_exception_response("1200", key)

    try:
        key_info = tornget("key/?selections=info", api_key)
        user_info = tornget("user/?selections=basic,discord", api_key)
    except NetworkingError as e:
        _log_auth(
            kwargs["user"].tid, AuthAction.API_KEY_ADD_FAILED, api_key, details=f"Torn networking error ({e.code})"
        )
        return make_exception_response("4100", key, details={"code": e.code, "message": e.message})
    except TornError as e:
        _log_auth(kwargs["user"].tid, AuthAction.API_KEY_ADD_FAILED, api_key, details=f"Torn error ({e.code})")
        return make_exception_response("4101", key, details={"code": e.code, "message": e.message})

    if key_info["access_level"] == 0:
        return make_exception_response("4002", key)
    elif user_info["player_id"] != kwargs["user"].tid:
        _log_auth(
            kwargs["user"].tid,
            AuthAction.API_KEY_ADD_FAILED_OTHER_USER,
            api_key,
            details=f"Other user ({user_info['player_id']})",
        )
        send_security_alert(user_info["discord"]["discordID"], user_info["player_id"], kwargs["user"].tid)
        return make_exception_response("4022", key)

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
        _log_auth(kwargs["user"].tid, AuthAction.API_KEY_ADD_SUCCESS, api_key)
    except IntegrityError:
        _log_auth(kwargs["user"].tid, AuthAction.API_KEY_ADD_FAILED, api_key, details="Integrity error")
        return make_exception_response("0000", key, details={"message": "Key already exists"})

    return (
        {"obfuscated_key": api_key[:6] + "*" * 10},
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
