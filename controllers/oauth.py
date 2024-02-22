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

import flask
import flask_login
from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.oauth2 import OAuth2Error

mod = flask.Blueprint("oauth_routes", __name__)
oauth_server = AuthorizationServer()

valid_scopes = ("identity",)


@mod.route("/oauth/authorize", methods=["GET", "POST"])
@flask_login.fresh_login_required
def oauth_authorize():
    if flask.request.method == "GET":
        scopes = []

        for scope in flask.request.args.get("scope", "").split(" "):
            scope = scope.lower()

            if scope == "":
                continue
            elif scope not in valid_scopes:
                return (
                    flask.render_template(
                        "errors/error.html",
                        title="Invalid Scope",
                        error=f"{scope} is not a valid OAuth scope for Tornium.",
                    ),
                    400,
                )

            scopes.append(scope)

        try:
            grant = oauth_server.get_consent_grant()
        except OAuth2Error as e:
            return e.error

        return flask.render_template("oauth/authorize.html", grant=grant, scopes=scopes)

    return oauth_server.create_authorization_response(grant_user=flask_login.current_user)


@mod.route("/oauth/token", methods=["POST"])
def issue_token():
    return oauth_server.create_token_response(request=flask.request)
