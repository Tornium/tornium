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

from authlib.integrations.flask_oauth2 import ResourceProtector as _ResourceProtector
from authlib.oauth2.rfc6750 import BearerTokenValidator as _BearerTokenValidator
from authlib.oauth2.rfc6750.errors import InvalidTokenError
from peewee import DoesNotExist

from ..models import OAuthToken


class BearerTokenValidator(_BearerTokenValidator):
    def authenticate_token(self, token_string: str) -> typing.Optional[OAuthToken]:
        """A method to query token from database with the given token string.
        Developers MUST re-implement this method. For instance::

            def authenticate_token(self, token_string):
                return get_token_from_database(token_string)

        :param token_string: A string to represent the access_token.
        :return: token
        """

        token: OAuthToken
        try:
            token = (
                OAuthToken.select()
                .where(
                    (OAuthToken.access_token == token_string)
                    & (OAuthToken.access_token_revoked_at.is_null(True))
                    & (OAuthToken.refresh_token_revoked_at.is_null(True))
                )
                .get()
            )
        except DoesNotExist:
            return None

        if token.consent is not None and (token.consent.revoked_at is not None or token.consent.revoked_by is not None):
            # If the token has a resource consent (for client credentials grant), we need
            # to ensure that it's still active as otherwise this token is effectively
            # revoked.

            return None

        return token


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
