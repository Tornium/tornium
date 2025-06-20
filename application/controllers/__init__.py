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

from flask import Blueprint, jsonify, render_template, request, send_from_directory
from flask_login import current_user, fresh_login_required
from peewee import DoesNotExist
from tornium_commons.models import OAuthClient, OAuthToken, Server, TornKey, User

from controllers.decorators import token_required

mod = Blueprint("baseroutes", __name__)


@mod.route("/")
@mod.route("/index")
def index():
    return render_template("index.html")


@mod.route("/terms")
def terms():
    return render_template("terms.html")


@mod.route("/privacy")
def privacy():
    return render_template("privacy.html")


@mod.route("/settings")
@fresh_login_required
@token_required(setnx=True)
def settings(*args, **kwargs):
    if current_user.key is None:
        obfuscated_key = "Not Set"
    else:
        obfuscated_key = current_user.key[:6] + "*" * 10

    api_keys = list(
        k
        for k in TornKey.select(
            TornKey.guid,
            TornKey.api_key,
            TornKey.access_level,
            TornKey.disabled,
            TornKey.paused,
            TornKey.default,
        )
        .join(User)
        .where(TornKey.user.tid == current_user.tid)
    )

    # Applications the user has authorized are:
    #  - belonging to the user
    #  - have a not-revoked access token OR have a not-revoked refresh token
    applications = list(
        token
        for token in OAuthToken.select()
        .distinct(OAuthToken.client)
        .where(
            (OAuthToken.user == current_user.tid)
            & (
                (OAuthToken.access_token_revoked_at.is_null(True))
                | (OAuthToken.refresh_token.is_null(False) & (OAuthToken.refresh_token_revoked_at.is_null(True)))
            )
        )
        .order_by(OAuthToken.client.asc(), OAuthToken.issued_at)
    )

    return render_template(
        "settings/settings.html",
        enabled_mfa=current_user.security,
        obfuscated_key=obfuscated_key,
        api_keys=api_keys,
        applications=applications,
        discord_linked=("Not Linked" if current_user.discord_id in ("", None, 0) else "Linked"),
    )


@mod.route("/settings/application/<application_id>")
@fresh_login_required
def settings_application(application_id: str, *args, **kwargs):
    try:
        current_token: OAuthToken = (
            OAuthToken.select()
            .where(
                (OAuthToken.user == current_user.tid)
                & (OAuthToken.client == application_id)
                & (
                    (OAuthToken.access_token_revoked_at.is_null(True))
                    | (OAuthToken.refresh_token.is_null(False) & (OAuthToken.refresh_token_revoked_at.is_null(True)))
                )
            )
            .order_by(OAuthToken.issued_at.desc())
            .get()
        )
        first_token: OAuthToken = (
            OAuthToken.select()
            .where((OAuthToken.user == current_user.tid) & (OAuthToken.client == application_id))
            .order_by(OAuthToken.issued_at.asc())
            .get()
        )
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Application ID",
                error="You have not authorized any application with this ID.",
            ),
            404,
        )

    scopes = current_token.scope.split()

    return render_template(
        "settings/application.html", current_token=current_token, first_token=first_token, scopes=scopes
    )


@mod.route("/static/favicon.svg")
@mod.route("/static/logo.svg")
@mod.route("/static/styles.css")
@mod.route("/static/utils.js")
@mod.route("/static/bot/armory.js")
@mod.route("/static/bot/notification.js")
@mod.route("/static/bot/oc.js")
@mod.route("/static/bot/guild.js")
@mod.route("/static/bot/verify.js")
@mod.route("/static/components/dynamic-list.js")
@mod.route("/static/components/table-viewer.js")
@mod.route("/static/faction/armory.js")
@mod.route("/static/faction/banking.js")
@mod.route("/static/faction/bankingaa.js")
@mod.route("/static/faction/bot.js")
@mod.route("/static/faction/chain.js")
@mod.route("/static/faction/members.js")
@mod.route("/static/fonts/JetBrainsMono-Light.woff2")
@mod.route("/static/global/api.js")
@mod.route("/static/global/discord.js")
@mod.route("/static/global/guilds.js")
@mod.route("/static/global/items.js")
@mod.route("/static/global/modeSelector.js")
@mod.route("/static/global/oc.js")
@mod.route("/static/global/utils.js")
@mod.route("/static/notification/trigger.js")
@mod.route("/static/notification/trigger-create.js")
@mod.route("/static/notification/trigger-server-add.js")
@mod.route("/static/settings/settings.js")
@mod.route("/static/settings/application.js")
@mod.route("/static/stats/db.js")
@mod.route("/static/stats/list.js")
@mod.route("/static/torn/factions.js")
@mod.route("/static/torn/users.js")
def static():
    return send_from_directory("static", request.path[8:])


@mod.route("/robots.txt")
def base_statics():
    return send_from_directory("static", request.path[1:])


@mod.route("/shields/server_count.json")
def shields_server_count():
    return jsonify(
        {
            "schemaVersion": 1,
            "label": "Server Count",
            "message": str(Server.select().count()),
        }
    )


@mod.route("/shields/user_count.json")
def shields_user_count():
    return jsonify(
        {
            "schemaVersion": 1,
            "label": "User Count",
            "message": str(TornKey.select().distinct(TornKey.user).count()),
        }
    )
