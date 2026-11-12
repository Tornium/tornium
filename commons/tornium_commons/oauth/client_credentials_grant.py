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
from authlib.oauth2.rfc6749 import grants, scope_to_list
from authlib.oauth2.rfc6749.errors import (
    InvalidRequestError,
    InvalidScopeError,
    UnauthorizedClientError,
)

from ..models import (
    AuthAction,
    OAuthClient,
    OAuthClientResourceConsent,
    OAuthToken,
    User,
)
from .log import log

GENERIC_RESOURCE_SCOPES: typing.Set[str] = {"identity"}
FACTION_RESOURCE_SCOPES: typing.Set[str] = {"faction", "faction:attacks", "faction:armory", "faction:crimes"}
SERVER_RESOURCE_SCOPES: typing.Set[str] = set()


def parse_resource(resource: str) -> typing.Tuple[typing.Optional[str], typing.Optional[int]]:
    if not isinstance(resource, str):
        return (None, None)

    resource_type, _, resource_raw_id = resource.partition(":")

    try:
        resource_id = int(resource_raw_id)
    except ValueError:
        raise InvalidRequestError(description="Invalid resource ID")

    if resource_type not in OAuthClientResourceConsent.RESOURCE_TYPES:
        raise InvalidRequestError(description="Unknown organization type")

    return (resource_type, resource_id)


class ClientCredentialsGrant(grants.ClientCredentialsGrant):
    # The machine-to-machine OAuth grant where a resource can consent for a token of
    # the client to provide access.
    # See https://docs.authlib.org/en/stable/oauth2/specs/rfc6749.html#authlib.oauth2.rfc6749.grants.ClientCredentialsGrant

    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]

    def validate_token_request(self):
        """The client makes a request to the token endpoint by adding the
        following parameters using the "application/x-www-form-urlencoded"
        format per Appendix B with a character encoding of UTF-8 in the HTTP
        request entity-body:

        grant_type
             REQUIRED.  Value MUST be set to "client_credentials".

        scope
             OPTIONAL.  The scope of the access request as described by
             Section 3.3.

        The client MUST authenticate with the authorization server as
        described in Section 3.2.1.

        For example, the client makes the following HTTP request using
        transport-layer security (with extra line breaks for display purposes
        only):

        .. code-block:: http

            POST /token HTTP/1.1
            Host: server.example.com
            Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW
            Content-Type: application/x-www-form-urlencoded

            grant_type=client_credentials

        The authorization server MUST authenticate the client.
        """

        self.request: FlaskOAuth2Request
        client: OAuthClient = self.request.client

        super().validate_token_request()

        # We need to now validate the resources and scopes requested for the client. We
        # can use authlib's implementation of validation as it does the basic checks
        # against the provided data and doesn't disrupt this validation.

        requested_scopes = set(scope_to_list(self.request.payload.scope) or [])

        requested_resource = self.request.payload.data.get("resource")
        resource_type, resource_id = parse_resource(requested_resource)

        if resource_type is None and resource_id is None:
            if not requested_scopes <= GENERIC_RESOURCE_SCOPES:
                raise InvalidScopeError(description="At least one of these scopes require a resource consent")

            self.request.resource_consent_binding = None
            return

        consent: typing.Optional[OAuthClientResourceConsent] = OAuthClientResourceConsent.get_consent(
            client.client_id, **{resource_type: resource_id}
        )

        if consent is None:
            raise UnauthorizedClientError(description="Client is not installed in this organization")
        elif not requested_scopes <= set(scope_to_list(consent.scope)):
            raise InvalidScopeError()

        self.request.consent_binding = consent
        return

    def create_token_response(self):
        """If the access token request is valid and authorized, the
        authorization server issues an access token as described in
        Section 5.1.  A refresh token SHOULD NOT be included.  If the request
        failed client authentication or is invalid, the authorization server
        returns an error response as described in Section 5.2.

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
                "example_parameter":"example_value"
            }

        :returns: an :class:`~authlib.oauth2.rfc6749.OAuth2Response`
        """

        token = self.generate_token(
            user=self.request.user, scope=self.request.scope, include_refresh_token=False, expires_in=3600
        )
        log(user_id=self.request.user.tid, action=AuthAction.OAUTH_TOKEN_ISSUE, request=self.request)

        return 200, token, self.TOKEN_RESPONSE_HEADER
