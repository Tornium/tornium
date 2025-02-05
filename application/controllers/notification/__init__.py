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

from controllers.notification import trigger

mod = Blueprint("notification_routes", __name__)

# Trigger Routes
mod.add_url_rule("/notification/trigger", view_func=trigger.triggers, methods=["GET"])
mod.add_url_rule("/notification/trigger/create", view_func=trigger.trigger_create, methods=["GET"])
mod.add_url_rule("/notification/trigger/view/<trigger_uuid>", view_func=trigger.trigger_get, methods=["GET"])
mod.add_url_rule("/notification/trigger/add/<trigger_uuid>", view_func=trigger.trigger_add_server, methods=["GET"])
mod.add_url_rule(
    "/notification/trigger/add/<trigger_uuid>/guild/<int:guild_id>",
    view_func=trigger.trigger_setup_server,
    methods=["GET"],
)


@mod.route("/notification")
def index():
    return render_template("notification/index.html")
