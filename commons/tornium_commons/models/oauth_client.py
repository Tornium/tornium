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

import secrets
import typing

from authlib.oauth2.rfc6749 import list_to_scope, scope_to_list
from peewee import DateTimeField, FixedCharField, ForeignKeyField
from playhouse.postgres_ext import JSONField

from .base_model import BaseModel
from .user import User


class OAuthClient(BaseModel):
    client_id = FixedCharField(max_length=48, primary_key=True)
    client_secret = FixedCharField(max_length=120)
    client_id_issued_at = DateTimeField(null=False)
    client_secret_expires_at = DateTimeField(null=True)
    client_metadata = JSONField()

    user = ForeignKeyField(User, null=False)

    @property
    def client_info(self):
        """Implementation for Client Info in OAuth 2.0 Dynamic Client
        Registration Protocol via `Section 3.2.1`_.

        .. _`Section 3.2.1`: https://tools.ietf.org/html/rfc7591#section-3.2.1
        """
        return dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            client_id_issued_at=self.client_id_issued_at,
            client_secret_expires_at=self.client_secret_expires_at,
        )

    @property
    def redirect_uris(self):
        return self.client_metadata.get("redirect_uris", [])

    @property
    def token_endpoint_auth_method(self):
        return self.client_metadata.get("token_endpoint_auth_method", "client_secret_basic")

    @property
    def grant_types(self):
        return self.client_metadata.get("grant_types", [])

    @property
    def response_types(self):
        return self.client_metadata.get("response_types", [])

    @property
    def client_name(self):
        return self.client_metadata.get("client_name")

    @property
    def client_uri(self):
        return self.client_metadata.get("client_uri")

    @property
    def logo_uri(self):
        return self.client_metadata.get("logo_uri")

    @property
    def scope(self):
        return self.client_metadata.get("scope", "")

    @property
    def contacts(self):
        return self.client_metadata.get("contacts", [])

    @property
    def tos_uri(self):
        return self.client_metadata.get("tos_uri")

    @property
    def policy_uri(self):
        return self.client_metadata.get("policy_uri")

    @property
    def jwks_uri(self):
        return self.client_metadata.get("jwks_uri")

    @property
    def jwks(self):
        return self.client_metadata.get("jwks", [])

    @property
    def software_id(self):
        return self.client_metadata.get("software_id")

    @property
    def software_version(self):
        return self.client_metadata.get("software_version")

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        if self.redirect_uris:
            return self.redirect_uris[0]

    def get_allowed_scope(self, scope):
        if not scope:
            return ""
        allowed = set(self.scope.split())
        scopes = scope_to_list(scope)
        return list_to_scope([s for s in scopes if s in allowed])

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in self.redirect_uris

    def check_client_secret(self, client_secret):
        return secrets.compare_digest(self.client_secret, client_secret)

    def check_endpoint_auth_method(self, method, endpoint):
        if endpoint == "token":
            return self.token_endpoint_auth_method == method

        return True

    def check_response_type(self, response_type):
        return response_type in self.response_types

    def check_grant_type(self, grant_type):
        return grant_type in self.grant_types

    @classmethod
    def get_client(cls, client_id: str) -> typing.Optional["OAuthClient"]:
        return OAuthClient.select().where(OAuthClient.client_id == client_id).first()

    # Custom properties below

    @property
    def official(self) -> bool:
        return self.client_metadata.get("official", False)

    @property
    def verified(self) -> bool:
        return self.client_metadata.get("verified", False)
