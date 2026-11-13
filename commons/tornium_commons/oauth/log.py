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

from authlib.integrations.flask_oauth2.requests import FlaskOAuth2Request
from peewee import DataError

from ..models import AuthAction, AuthLog


def log(user_id: typing.Optional[int], action: AuthAction, request: FlaskOAuth2Request, login_key=None) -> None:
    now = datetime.datetime.utcnow()

    try:
        AuthLog.insert(
            user=user_id,
            timestamp=now,
            ip=request._request.headers.get("CF-Connecting-IP") or request._request.remote_addr,
            action=action.value,
            login_key=login_key,
            details=request.payload.client_id,
        ).execute()
    except DataError:
        # Some IP addresses are larger than the data field
        AuthLog.insert(
            user=user_id,
            timestamp=now,
            ip=None,
            action=action.value,
            login_key=login_key,
            details=request.payload.client_id,
        ).execute()

    return
