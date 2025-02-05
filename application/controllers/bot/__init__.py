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

from flask import Blueprint, render_template

from controllers.bot import armory, guild, notification, oc, verify

mod = Blueprint("botroutes", __name__)

# Armory Routes
mod.add_url_rule(
    "/bot/dashboard/<string:guild_id>/armory",
    view_func=armory.armory_dashboard,
    methods=["GET"],
)

# Guild Routes
mod.add_url_rule("/bot/dashboard", view_func=guild.dashboard, methods=["GET"])
mod.add_url_rule(
    "/bot/dashboard/<string:guild_id>",
    view_func=guild.guild_dashboard,
    methods=["GET"],
)

# Verify Routes
mod.add_url_rule(
    "/bot/dashboard/<string:guild_id>/verify",
    view_func=verify.verify_dashboard,
    methods=["GET"],
)

# OC Routes
mod.add_url_rule(
    "/bot/dashboard/<string:guild_id>/oc",
    view_func=oc.oc_dashboard,
    methods=["GET"],
)

# Notification Routes
mod.add_url_rule(
    "/bot/dashboard/<string:guild_id>/notification",
    view_func=notification.notification_dashboard,
    methods=["GET"],
)
mod.add_url_rule(
    "/bot/dashboard/<int:guild_id>/notification/<notification_uuid>",
    view_func=notification.view_notification,
    methods=["GET"],
)


@mod.route("/bot")
def index():
    return render_template("bot/index.html")
