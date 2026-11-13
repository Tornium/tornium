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
import uuid

import flask
import flask_login
from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6749 import scope_to_list
from authlib.oauth2.rfc6749.errors import (
    InvalidClientError,
    InvalidGrantError,
    InvalidRequestError,
)
from authlib.oauth2.rfc6749.grants import BaseGrant
from flask import abort, redirect, render_template, request
from flask_login import current_user, fresh_login_required
from peewee import DoesNotExist
from tornium_commons.models import (
    Faction,
    OAuthClient,
    OAuthClientResourceConsent,
    Server,
)
from tornium_commons.oauth.client_credentials_grant import parse_resource
from tornium_commons.oauth.scopes import RESOURCE_SCOPES

mod = flask.Blueprint("oauth_routes", __name__)
oauth_server = AuthorizationServer()

valid_scopes = (
    "identity",
    # Faction scopes
    "faction",
    "faction:armory",
    "faction:attacks",
    "faction:banking",
    "faction:crimes",
    # API key scopes
    "torn_key:usage",
)


@mod.route("/.well-known/openid-configuration", methods=["GET"])
def openid_configuration():
    """
    Endpoint to handle OpenID (and OAuth2) provider discovery.

    See: https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfig
    """
    return (
        flask.jsonify(
            {
                "issuer": "https://tornium.com",
                "authorization_endpoint": "https://tornium.com/oauth/authorize",
                "token_endpoint": "https://tornium.com/oauth/token",  # nosec B105
                "scopes_supported": list(valid_scopes),
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "client_credentials"],
                "service_documentation": "https://docs.tornium.com/reference/api/oauth-provider.html",
                "op_privacy_uri": "https://tornium.com/privacy",
                "op_tos_uri": "https://tornium.com/terms",
            }
        ),
        200,
        {"Content-Type": "application/json"},
    )


@mod.route("/oauth/authorize", methods=["GET", "POST"])
@flask_login.fresh_login_required
def oauth_authorize():
    try:
        grant: BaseGrant = oauth_server.get_consent_grant(end_user=flask_login.current_user)
    except OAuth2Error as error:
        return oauth_server.handle_error_response(flask.request, error)

    if flask.request.method == "GET":
        scopes = [scope for scope in grant.client.get_allowed_scope(grant.request.scope).split()]

        return flask.render_template("oauth/authorize.html", grant=grant, scopes=scopes)

    return oauth_server.create_authorization_response(grant_user=flask_login.current_user)


@mod.route("/oauth/token", methods=["POST"])
def issue_token():
    return oauth_server.create_token_response(request=flask.request)


@mod.route("/oauth/<client_id>/callback")
def client_callback(client_id: str):
    client: OAuthClient = oauth_server.query_client(client_id)

    if client is None:
        return oauth_server.handle_error_response(oauth_server.create_json_request(flask.request), InvalidClientError())
    elif client.token_endpoint_auth_method != "none":  # nosec B105
        return oauth_server.handle_error_response(oauth_server.create_json_request(flask.request), InvalidClientError())
    elif not client.check_redirect_uri(flask.request.base_url):
        return oauth_server.handle_error_response(oauth_server.create_json_request(flask.request), InvalidGrantError())

    return flask.render_template("oauth/callback.html", client=client)


@mod.route("/oauth/<client_id>/consent", methods=["GET", "POST"])
@fresh_login_required
def client_consent(client_id: str):
    client: OAuthClient = oauth_server.query_client(client_id)

    if client is None:
        return (
            render_template(
                "errors/error.html", title="Invalid Client", error="The provided OAuth client does not exist."
            ),
            400,
        )
    elif not client.check_grant_type("client_credentials"):
        return (
            render_template(
                "errors/error.html",
                title="Invalid Client",
                error="The provided OAuth client has an incorrect grant type.",
            ),
            400,
        )

    requested_scopes = set(scope_to_list(request.args.get("scope", "")) or []) & client.scope_list()

    try:
        resource_type, resource_id = parse_resource(request.args["resource"])
    except InvalidRequestError:
        return (
            render_template(
                "errors/error.html", title="Invalid Resource", error="The provided resource was not valid."
            ),
            400,
        )
    except KeyError:
        # There is no resource provided so there is nothing to consent for.
        return (
            render_template(
                "errors/error.html", title="Invalid Resource", error="There is no resource consent is requested for."
            ),
            400,
        )

    if not OAuthClientResourceConsent.is_allowed_consent(current_user, resource_type, resource_id):
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error=f"You do not have sufficient permissions to grant consent for this resource ({resource_type} ID {resource_id})",
            ),
            403,
        )

    valid_requested_scopes = requested_scopes & RESOURCE_SCOPES[resource_type]
    if len(valid_requested_scopes) == 0:
        return (
            render_template(
                "errors/error.html", title="Invalid Scopes", error=f"No {resource_type} scopes were requested"
            ),
            400,
        )

    existing_consent: typing.Optional[OAuthClientResourceConsent] = OAuthClientResourceConsent.get_consent(
        client.client_id, **{resource_type: resource_id}
    )

    if request.method == "GET":
        if resource_type == "faction":
            resource_name = Faction.select(Faction.name).where(Faction.tid == resource_id).scalar()
            consent_page = "/faction/consent"
        else:
            resource_name = Server.select(Server.name).where(Server.sid == resource_id).scalar()
            consent_page = f"/bot/dashboard/{resource_id}/consent"

        return flask.render_template(
            "oauth/consent.html",
            client=client,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            consent_page=consent_page,
            requested_scopes=valid_requested_scopes,
            existing_scopes=[] if existing_consent is None else existing_consent.scopes,
        )

    if flask.request.form.get("csrf-token") != flask.session.get("csrf_token"):
        abort(403)

    # Checkboxes let the admin approve a subset of the scopes which would be used
    # for consent instead of the scopes requested.
    approved_scopes = set(flask.request.form.getlist("scopes")) & valid_requested_scopes
    if not approved_scopes:
        return (
            render_template(
                "errors/error.html", title="Permission Denied", error="None of the requested scopes were approved"
            ),
            400,
        )

    granted_consent: OAuthClientResourceConsent = OAuthClientResourceConsent.grant(
        client.client_id, current_user, resource_type, resource_id, approved_scopes
    )

    return flask.render_template(
        "oauth/consent-granted.html",
        client=client,
        resource_type=resource_type,
        resource_id=resource_id,
        consent=granted_consent,
    )


@mod.route("/oauth/<client_id>/consent/<consent_id>/revoke", methods=["POST"])
@fresh_login_required
def revoke_consent(client_id: str, consent_id: str):
    if flask.request.form.get("csrf-token") != flask.session.get("csrf_token"):
        return abort(403)

    try:
        consent: OAuthClientResourceConsent = (
            OAuthClientResourceConsent.select()
            .where(
                (OAuthClientResourceConsent.guid == uuid.UUID(consent_id))
                & (OAuthClientResourceConsent.client == client_id)
                & (OAuthClientResourceConsent.revoked_at.is_null(True))
            )
            .get()
        )
    except (DoesNotExist, ValueError):
        return (
            render_template("errors/error.html", title="Invalid Consent", error="No matching consent could be found."),
            404,
        )

    consent_resource_type, consent_resource_id = consent.resource

    if not OAuthClientResourceConsent.is_allowed_consent(current_user, consent_resource_type, consent_resource_id):
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error=f"You do not have sufficient permissions to revoke consent for this resource ({consent_resource_type} ID {consent_resource_id})",
            ),
            403,
        )

    consent.revoke(current_user)

    if consent_resource_type == "faction":
        return redirect("/faction/consent", code=303)
    elif consent_resource_type == "server":
        return redirect(f"/bot/dashboard/{consent_resource_id}/consent", code=303)
