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

from authlib.integrations.flask_oauth2.requests import FlaskOAuth2Request
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6749.errors import InvalidGrantError

from ..models import AuthAction, OAuthAuthorizationCode, OAuthToken, User
from .log import log


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post", "none"]

    def save_authorization_code(self, code, request: FlaskOAuth2Request):
        code_challenge = request.payload.data.get("code_challenge")
        code_challenge_method = request.payload.data.get("code_challenge_method")
        auth_code = OAuthAuthorizationCode.insert(
            code=code,
            client_id=request.payload.client_id,
            redirect_uri=request.payload.redirect_uri,
            scope=request.payload.scope or "",
            user=request.user.tid,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            used_at=None,
            used_by=None,
        ).execute()

        log(user_id=request.user.tid, action=AuthAction.OAUTH_AUTHORIZATION_SUCCESS, request=request)

        return auth_code

    def query_authorization_code(self, code, client):
        item = (
            OAuthAuthorizationCode.select()
            .join(User)
            .where((OAuthAuthorizationCode.code == code) & (OAuthAuthorizationCode.client_id == client.client_id))
            .first()
        )

        if item and not item.is_expired():
            return item

        return None

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
            expires_in=30 * 60 if client.check_grant_type("refresh_token") else 7 * 24 * 60 * 60,
        )

        # Since authlib doesn't support this yet, we need to manually insert this into the
        # generated token. See: https://github.com/authlib/authlib/issues/686
        token["refresh_token_expires_in"] = None
        if client.check_grant_type("refresh_token"):
            token["refresh_token_expires_in"] = 24 * 60 * 60

        saved_token = self.save_token(token)
        authorization_code.mark_created(saved_token)

        log(user_id=self.request.user.tid, action=AuthAction.OAUTH_TOKEN_ISSUE, request=self.request)

        # NOTE: the authorization code should not be deleted for auditability and to allow for deletion of
        # access tokens created by the authorization code when the authorization code is reused
        # self.delete_authorization_code(authorization_code)

        return 200, token, self.TOKEN_RESPONSE_HEADER
