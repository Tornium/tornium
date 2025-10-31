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
import hashlib
import json
import secrets
import typing
import urllib.parse

from authlib.oauth2.rfc6749 import list_to_scope
from flask import render_template, request
from flask_login import current_user, fresh_login_required, login_required
from peewee import DoesNotExist
from tornium_commons.models import OAuthClient

from controllers.api.v1.utils import make_exception_response
from controllers.oauth import valid_scopes


def validate_oauth_redirect_uri(uri: str) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Validate a URI to act as a redirect URI for OAuth2.

    See https://www.rfc-editor.org/rfc/rfc6749#section-3.1.2
    """
    try:
        parsed_uri = urllib.parse.urlparse(uri)
    except ValueError:
        return (False, "the URI was not able to be parsed")

    if not parsed_uri.scheme or not parsed_uri.netloc:
        # RFC6749 3.1.2: The redirection endpoint URI MUST be an absolute URI
        # RFC3986 4.2: absolute-URI = scheme ":" hier-part [ "?" query ]
        return (False, "the URI **MUST** be an absolute URI")
    elif parsed_uri.fragment:
        # RFC6749 3.1.2: The endpoint URI MUST NOT include a fragment component.
        return (False, "the URI **MUST** NOT include a fragment")
    elif parsed_uri.scheme == "http" and parsed_uri.hostname not in ("localhost", "127.0.0.1"):
        # RFC6749 3.1.3: The redirection endpoint SHOULD require the use of TLS
        # However, we can not require only HTTPS to allow for native applications with custom schemas.
        # For ease of use, localhost will be allowed without HTTPs.
        return (False, "the URI must use TLS unless using a loopback address")
    elif parsed_uri.params != "" or parsed_uri.query != "":
        # RFC9700 2.1: Clients and authorization servers MUST NOT expose URLs that forward the user's browser to arbitrary URIs obtained from a query parameter
        return (False, "the URI must not use query parameters")

    return (True, None)


@login_required
def clients_list():
    clients = [
        _client
        for _client in OAuthClient.select().where(
            (OAuthClient.user_id == current_user.tid) & (OAuthClient.deleted_at.is_null(True))
        )
    ]

    return render_template("/developers/clients.html", clients=clients)


@fresh_login_required
def new_client():
    return render_template("/developers/new-client.html")


@fresh_login_required
def create_client():
    data = json.loads(request.get_data().decode("utf-8"))

    client_name = data.get("client_name")
    client_type = data.get("client_type")

    if client_name is None or not isinstance(client_name, str):
        return make_exception_response("1000", details={"message": "Invalid client name"})
    elif client_type is None or not isinstance(client_type, str):
        return make_exception_response("1000", details={"message": "Invalid client type"})

    if client_type == "authorization-code-grant":
        grant = "code"
        auth_method = "client_secret_basic"
    elif client_type == "authorization-code-grant-pkce":
        grant = "code"
        auth_method = "none"
    elif client_type == "device-authorization-grant":
        grant = "urn:ietf:params:oauth:grant-type:device_code"
        auth_method = "none"
    else:
        return make_exception_response(
            "1000",
            details={
                "message": "Invalid client type. Must be authorization code grant (w/ optional PKCE) or device authorization grant."
            },
        )

    client: OAuthClient = OAuthClient.create(
        client_id=secrets.token_hex(24),  # Each byte is two characters
        client_secret=None,  # The client secret should be generated later so that it can be hashed in the database
        client_id_issued_at=datetime.datetime.utcnow(),
        client_secret_expires_at=None,
        client_metadata={
            "client_name": client_name,
            "client_uri": "",
            "grant_types": [grant],
            "redirect_uris": [],
            "response_types": [],
            "scope": "",
            "token_endpoint_auth_method": auth_method,
            "official": False,
            "verified": False,
        },
        user=current_user.tid,
    )

    return {"client_id": client.client_id}, 201


@fresh_login_required
def regenerate_client_secret(client_id: str):
    try:
        client: OAuthClient = (
            OAuthClient.select()
            .where((OAuthClient.client_id == client_id) & (OAuthClient.deleted_at.is_null(True)))
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1500")

    if client.user_id != current_user.tid:
        return make_exception_response("4022")

    client_secret = secrets.token_hex(60)  # Each byte is two characters
    hashed_client_secret = hashlib.sha256(client_secret.encode("utf-8")).hexdigest()

    OAuthClient.update(client_secret=hashed_client_secret).where(OAuthClient.client_id == client_id).execute()

    return {"client_secret": client_secret}, 200


@fresh_login_required
def delete_client(client_id: str):
    try:
        client: OAuthClient = (
            OAuthClient.select()
            .where((OAuthClient.client_id == client_id) & (OAuthClient.deleted_at.is_null(True)))
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1500")

    if client.user_id != current_user.tid:
        return make_exception_response("4022")

    client.soft_delete()
    return "", 204


@fresh_login_required
def update_client(client_id: str):
    data = json.loads(request.get_data().decode("utf-8"))

    try:
        client: OAuthClient = (
            OAuthClient.select()
            .where((OAuthClient.client_id == client_id) & (OAuthClient.deleted_at.is_null(True)))
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1500")

    if client.user_id != current_user.tid:
        return make_exception_response("4022")

    client_name = data.get("client_name")
    client_redirect_uris = data.get("client_redirect_uris")
    client_scopes = data.get("client_scopes")
    client_uri = data.get("client_uri")
    client_terms_uri = data.get("client_terms_uri")
    client_privacy_uri = data.get("client_privacy_uri")

    if not isinstance(client_name, str) or len(client_name) == 0 or len(client_name) >= 64:
        return make_exception_response(
            "1000",
            details={
                "message": "The provided client name was not valid. The name must be between 1 and 64 characters long."
            },
        )
    elif (
        not isinstance(client_redirect_uris, list)
        or any(not isinstance(uri, str) for uri in client_redirect_uris)
        or any(not validate_oauth_redirect_uri(uri)[0] for uri in client_redirect_uris)
    ):
        return make_exception_response(
            "1000", details={"message": "At least one of the provided redirect URIs was not valid."}
        )
    elif (
        not isinstance(client_scopes, list)
        or any(not isinstance(scope, str) for scope in client_scopes)
        or any(scope not in valid_scopes for scope in client_scopes)
    ):
        return make_exception_response(
            "1000", details={"message": "At least one of the provided scopes was not valid."}
        )
    elif isinstance(client_uri, str) and client_uri != "" and not validate_oauth_redirect_uri(client_uri)[0]:
        (valid_uri, invalid_reason) = validate_oauth_redirect_uri(client_uri)
        return make_exception_response(
            "1000", details={"message": f"The provided client URI was not valid as {invalid_reason}"}
        )
    elif client_uri == "":
        client_uri = None
    elif (
        isinstance(client_terms_uri, str)
        and client_terms_uri != ""
        and not validate_oauth_redirect_uri(client_terms_uri)[0]
    ):
        (valid_uri, invalid_reason) = validate_oauth_redirect_uri(client_terms_uri)
        return make_exception_response(
            "1000", details={"message": f"The provided client terms of service URI was not valid as {invalid_reason}"}
        )
    elif client_terms_uri == "":
        client_terms_uri = None
    elif (
        isinstance(client_privacy_uri, str)
        and client_privacy_uri != ""
        and not validate_oauth_redirect_uri(client_privacy_uri)[0]
    ):
        (valid_uri, invalid_reason) = validate_oauth_redirect_uri(client_privacy_uri)
        return make_exception_response(
            "1000", details={"message": f"The provided client privacy policy URI was not valid as {invalid_reason}"}
        )
    elif client_privacy_uri == "":
        client_privacy_uri = None

    updated_client_metadata = {
        "redirect_uris": client_redirect_uris,
        "client_name": client_name,
        "client_uri": client_uri,
        "scope": list_to_scope(client_scopes),
        "tos_uri": client_terms_uri,
        "privacy_uri": client_privacy_uri,
    }

    OAuthClient.update(client_metadata=OAuthClient.client_metadata.concat(updated_client_metadata)).where(
        OAuthClient.client_id == client_id
    ).execute()

    return "", 204


@fresh_login_required
def client_dashboard(client_id: str):
    try:
        client: OAuthClient = (
            OAuthClient.select()
            .where((OAuthClient.client_id == client_id) & (OAuthClient.deleted_at.is_null(True)))
            .get()
        )
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Client ID",
                error="The provided client ID did not match any valid clients.",
            ),
            400,
        )

    if client.user.tid != current_user.tid:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error=f"{current_user.name} [{current_user.tid}] is not the owner of this client.",
            ),
            403,
        )

    return render_template("/developers/client_dashboard.html", client=client)
