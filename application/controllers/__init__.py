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
from tornium_commons.models import Server, TornKey

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
