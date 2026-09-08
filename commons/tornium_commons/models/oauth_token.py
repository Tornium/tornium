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
import time
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

from ..skyutils import SKYNET_WARNING
from .auth_log import AuthAction, AuthLog
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
    refresh_token_expires_in = BigIntegerField(null=True, default=None)

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

    def is_refresh_token_expired(self):
        if not self.refresh_token_expires_in:
            return False

        expires_at = self.issued_at + datetime.timedelta(seconds=self.refresh_token_expires_in)
        return expires_at < datetime.datetime.utcnow()

    def is_refresh_token_valid(self) -> bool:
        # The refresh token is still valid as long as it hasn't been revoked as the access
        # token would be revoked once it expires long before the refresh token expires.

        return self.refresh_token_revoked_at is None and not self.is_refresh_token_expired()

    def revoke(self) -> None:
        now = datetime.datetime.utcnow()
        OAuthToken.update(access_token_revoked_at=now, refresh_token_revoked_at=now).where(
            OAuthToken.access_token == self.access_token
        ).execute()

        AuthLog.insert(
            user=self.user.tid,
            timestamp=now,
            ip=None,
            action=AuthAction.OAUTH_TOKEN_REVOKE.value,
            login_key=None,
            details=self.client.client_id,
        ).execute()

    def revoke_token_family(self) -> None:
        now = datetime.datetime.utcnow()
        OAuthToken.update(access_token_revoked_at=now, refresh_token_revoked_at=now).where(
            OAuthToken.family_id == self.family_id
        ).execute()

        AuthLog.insert(
            user=self.user.tid,
            timestamp=now,
            ip=None,
            action=AuthAction.OAUTH_TOKEN_REFRESH_REUSE.value,
            login_key=str(self.family_id),
            details=self.client.client_id,
        ).execute()

    def alert_token_family_revocation(self) -> None:
        from tornium_celery.tasks.misc import send_dm

        if self.user.discord_id in (None, 0):
            # Since the user doesn't have a Discord ID, we are unable to alert them.
            return

        discord_payload = {
            "embeds": [
                {
                    "title": "Security Alert",
                    "description": f"Someone has attempted to re-use an OAuth refresh token belonging to your Torn account (ID {self.user_id}) to generate a new OAuth access token <t:{int(time.time())}. For more information, see the [Tornium documentation]. If this was not intended or you don't understand this, please contact the developer as soon as possible. As a precaution, all of your Tornium OAuth access token related to this token have been revoked, and you may need to re-authorize applications logged in through Tornium.",
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

        send_dm.delay(self.user.discord_id, discord_payload)
        return

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
