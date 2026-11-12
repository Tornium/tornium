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

import typing

from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6749.errors import InvalidGrantError
from peewee import DoesNotExist

from ..models import AuthAction, OAuthToken, User
from .log import log


class RefreshTokenGrant(grants.RefreshTokenGrant):
    INCLUDE_NEW_REFRESH_TOKEN = True
    TOKEN_ENDPOINT_AUTH_METHODS = ["none", "client_secret_post", "client_secret_basic"]

    def authenticate_refresh_token(self, refresh_token: str) -> typing.Optional[OAuthToken]:
        if refresh_token is None:
            return None

        try:
            token: OAuthToken = OAuthToken.select().where(OAuthToken.refresh_token == refresh_token).get()
        except DoesNotExist:
            log(
                user_id=self.request.user.tid if self.request.user is not None else None,
                action=AuthAction.OAUTH_TOKEN_REFRESH_INVALID,
                request=self.request,
            )
            return None

        if token.refresh_token_revoked_at is not None:
            # This refresh token has already (presumably) been used already as it is revoked, so
            # we should revoke all tokens of the family.
            # See RFC 9700 4.14.2:
            #
            # Authorization servers MUST utilize one of these methods to detect refresh token
            # replay by malicious actors (for public clients):
            #
            # Refresh token rotation: the authorization server issues a new refresh token with
            # every access token refresh response. The previous refresh token is invalidated,
            # but information about the relationship is retained by the authorization server. If
            # a refresh token is compromised and subsequently used by both the attacker and the
            # legitimate client, one of them will present an invalidated refresh token, which will
            # inform the authorization server of the breach. The authorization server cannot determine
            # which party submitted the invalid refresh token, but it will revoke the active refresh
            # token. This stops the attack at the cost of forcing the legitimate client to obtain a
            # fresh authorization grant.

            log(
                user_id=self.request.user.tid if self.request.user is not None else None,
                action=AuthAction.OAUTH_TOKEN_REFRESH_REUSE,
                login_key=refresh_token,
                request=self.request,
            )

            token.revoke_token_family()
            token.alert_token_family_revocation()

            return None
        elif not token.is_refresh_token_valid():
            # This refresh token has expired (or has already been used, but that has already been
            # hndled above), so we should log it ane return None.
            log(
                user_id=self.request.user.tid if self.request.user is not None else None,
                action=AuthAction.OAUTH_TOKEN_REFRESH_INVALID,
                request=self.request,
            )

            return None

        return token

    def authenticate_user(self, refresh_token: OAuthToken) -> User:
        return refresh_token.user

    def revoke_old_credential(self, refresh_token: OAuthToken):
        refresh_token.revoke()

    def create_token_response(self):
        """
        If valid and authorized, the authorization server issues an access
        token as described in Section 5.1.  If the request failed
        verification or is invalid, the authorization server returns an error
        response as described in Section 5.2.
        """
        client = self.request.client
        refresh_token = self.request.refresh_token

        user = self.authenticate_user(refresh_token)
        if not user:
            raise InvalidGrantError("There is no 'user' for this code.")
        self.request.user = user

        scope = self.request.payload.scope
        if not scope:
            scope = refresh_token.get_scope()

        token = self.generate_token(
            user=user,
            scope=scope,
            include_refresh_token=client.check_grant_type("refresh_token"),
            expires_in=30 * 60 if client.check_grant_type("refresh_token") else 7 * 24 * 60 * 60,
        )

        # Since authlib doesn't support this yet, we need to manually insert this into the
        # generated token. See: https://github.com/authlib/authlib/issues/686
        token["refresh_token_expires_in"] = None
        if client.check_grant_type("refresh_token"):
            token["refresh_token_expires_in"] = 24 * 60 * 60

        self.save_token(token)
        self.revoke_old_credential(refresh_token)

        log(user_id=self.request.user.tid, action=AuthAction.OAUTH_TOKEN_REFRESH, request=self.request)

        # We should return the unmodified token without the refresh_token_expires_in to ensure other
        # authlib code handles it correctly.
        return 200, token, self.TOKEN_RESPONSE_HEADER
