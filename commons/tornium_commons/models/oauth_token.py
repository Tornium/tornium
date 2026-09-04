# BSD 3-Clause License
# Part of lepture/authlib
#
# Copyright (c) 2017, Hsiaoming Yang
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
import uuid

from authlib.integrations.flask_oauth2.requests import FlaskOAuth2Request
from peewee import (
    BigIntegerField,
    CharField,
    DateTimeField,
    FixedCharField,
    ForeignKeyField,
    TextField,
)
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel
from .oauth_client import OAuthClient
from .user import User


class OAuthToken(BaseModel):
    client = ForeignKeyField(OAuthClient, null=False)
    token_type = CharField(max_length=40)
    access_token = FixedCharField(max_length=255, unique=True, null=False)
    refresh_token = FixedCharField(max_length=255, index=True, null=True)
    scope = TextField(default="")
    issued_at = DateTimeField(null=False, default=datetime.datetime.utcnow)
    access_token_revoked_at = DateTimeField(null=True)
    refresh_token_revoked_at = DateTimeField(null=True)
    expires_in = BigIntegerField(null=False, default=0)

    user = ForeignKeyField(User, null=False)

    family_id = UUIDField(null=False)

    def check_client(self, client: OAuthClient):
        return self.client_id == client.get_client_id()

    def get_scope(self):
        return self.scope

    def get_expires_in(self):
        return self.expires_in

    def is_revoked(self):
        return self.access_token_revoked_at is not None or self.refresh_token_revoked_at is not None

    def is_expired(self):
        if not self.expires_in:
            return False

        expires_at = self.issued_at + datetime.timedelta(seconds=self.expires_in)
        return expires_at < datetime.datetime.utcnow()

    def is_refresh_token_valid(self) -> bool:
        return not self.is_revoked() and not self.is_expired()

    def revoke(self) -> None:
        OAuthToken.update(
            access_token_revoked_at=datetime.datetime.utcnow(), refresh_token_revoked_at=datetime.datetime.utcnow()
        ).where(OAuthToken.access_token == self.access_token).execute()

    def revoke_token_family(self) -> None:
        now = datetime.datetime.utcnow()
        OAuthToken.update(access_token_revoked_at=now, refresh_token_revoked_at=now).where(
            OAuthToken.family_id == self.family_id
        ).execute()

    @staticmethod
    def save_token(token_data, request: FlaskOAuth2Request):
        user_id = request.user.get_user_id() if request.user else None

        family_id = uuid.uuid4()
        if request.grant_type == "refresh_token":
            # If the original token is performed with a refresh token, we want to re-use the family ID of that
            # refresh token for this new token so that they're linked together in case it needs to be revoked.
            old_refresh_token = request.data.get("refresh_token")
            old_token: typing.Optional[OAuthToken] = (
                OAuthToken.select(OAuthToken.family_id)
                .where((OAuthToken.refresh_token == old_refresh_token) & (OAuthToken.refresh_token.is_null(False)))
                .first()
            )

            if old_token is not None:
                family_id = old_token.family_id

        return (
            OAuthToken.insert(client_id=request.client.client_id, user_id=user_id, family_id=family_id, **token_data)
            .returning(OAuthToken)
            .execute()[0]
        )
