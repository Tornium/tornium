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

from flask import render_template, request
from flask_login import current_user, fresh_login_required, login_required
from peewee import DoesNotExist
from tornium_commons.models import OAuthClient

from controllers.api.v1.utils import make_exception_response


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
