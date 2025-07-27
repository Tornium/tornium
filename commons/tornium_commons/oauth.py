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

import logging
import typing

from authlib.integrations.flask_oauth2 import ResourceProtector as _ResourceProtector
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6749.errors import InvalidGrantError
from authlib.oauth2.rfc6750 import BearerTokenValidator as _BearerTokenValidator
from authlib.oauth2.rfc6750.errors import InvalidTokenError

from .models import OAuthAuthorizationCode, OAuthToken, User


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post", "none"]

    def save_authorization_code(self, code, request):
        client = request.client
        code_challenge = request.data.get("code_challenge")
        code_challenge_method = request.data.get("code_challenge_method")
        auth_code = OAuthAuthorizationCode.insert(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user=request.user.tid,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            used_at=None,
            used_by=None,
        ).execute()

        return auth_code

    def query_authorization_code(self, code, client):
        item = (
            OAuthAuthorizationCode.select()
            .where((OAuthAuthorizationCode.code == code) & (OAuthAuthorizationCode.client_id == client.client_id))
            .first()
        )

        if item and not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        # NOTE: This should not be implemented. Authorization codes should never be deleted, only expired.
        return

    def authenticate_user(self, authorization_code):
        return authorization_code.user

    def create_token_response(self):
        """If the access token request is valid and authorized, the
        authorization server issues an access token and optional refresh
        token as described in Section 5.1.  If the request client
        authentication failed or is invalid, the authorization server returns
        an error response as described in Section 5.2. Per `Section 4.1.4`_.

        An example successful response:

        .. code-block:: http

            HTTP/1.1 200 OK
            Content-Type: application/json
            Cache-Control: no-store
            Pragma: no-cache

            {
                "access_token":"2YotnFZFEjr1zCsicMWpAA",
                "token_type":"example",
                "expires_in":3600,
                "refresh_token":"tGzv3JOkF0XG5Qx2TlKWIA",
                "example_parameter":"example_value"
            }

        :returns: (status_code, body, headers)

        .. _`Section 4.1.4`: https://tools.ietf.org/html/rfc6749#section-4.1.4
        """
        client = self.request.client
        authorization_code = self.request.authorization_code

        user = self.authenticate_user(authorization_code)
        if not user:
            raise InvalidGrantError("There is no 'user' for this code.")
        self.request.user = user

        authorization_code.used_by: typing.Optional[OAuthToken]
        if authorization_code.used_by is not None:
            authorization_code.used_by.revoke()
            raise InvalidGrantError("This authorization_code has already been used.")

        scope = authorization_code.get_scope()
        token = self.generate_token(
            user=user,
            scope=scope,
            include_refresh_token=client.check_grant_type("refresh_token"),
        )
        logging.getLogger(__name__).debug("Issue token %r to %r", token, client)

        saved_token = self.save_token(token)
        authorization_code.mark_created(saved_token)

        # NOTE: the authorization code should not be deleted for auditability and to allow for deletion of
        # access tokens created by the authorization code when the authorization code is reused
        # self.delete_authorization_code(authorization_code)

        return 200, token, self.TOKEN_RESPONSE_HEADER


class RefreshTokenGrant(grants.RefreshTokenGrant):
    INCLUDE_NEW_REFRESH_TOKEN = True
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_post", "client_secret_basic"]

    def authenticate_refresh_token(self, refresh_token: str) -> typing.Optional[OAuthToken]:
        token: typing.Optional[OAuthToken] = (
            OAuthToken.select().where(OAuthToken.refresh_token == refresh_token).first()
        )

        if token and token.is_refresh_token_valid():
            return token

    def authenticate_user(self, refresh_token: OAuthToken) -> User:
        return OAuthToken.user

    def revoke_old_credential(self, refresh_token: OAuthToken):
        OAuthToken.update(is_revoked=True).where(OAuthToken.access_token == refresh_token.access_token).execute()


class BearerTokenValidator(_BearerTokenValidator):
    def authenticate_token(self, token_string: str) -> typing.Optional[OAuthToken]:
        return OAuthToken.select().where(OAuthToken.access_token == token_string).first()


class CustomTokenValidator(_BearerTokenValidator):
    @staticmethod
    def scope_insufficient(token_scopes, required_scopes):
        # Session requests to API are guaranteed to have sufficient scope
        return False

    def authenticate_token(self, token_string: str):
        return token_string

    def validate_token(self, token, scopes, request):
        """Check if token is active and matches the requested scopes."""
        from flask import session

        if session.get("csrf_token") != token:
            raise InvalidTokenError(realm=self.realm, extra_attributes=self.extra_attributes)


class ResourceProtector(_ResourceProtector):
    def parse_request_authorization(self, request):
        """Parse the token and token validator from request Authorization header.
        Here is an example of Authorization header::

            Authorization: Bearer a-token-string

        This method will parse this header, if it can find the validator for
        ``Bearer``, it will return the validator and ``a-token-string``.

        :return: validator, token_string
        :raise: MissingAuthorizationError
        :raise: UnsupportedTokenTypeError
        """

        auth = request.headers.get("Authorization")
        csrf = request.headers.get("X-CSRF-Token") or request.headers.get("CSRF-Token")

        if not auth and csrf:
            return CustomTokenValidator(), csrf

        return super().parse_request_authorization(request)
