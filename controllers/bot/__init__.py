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

from flask import Blueprint, render_template

from controllers.bot import assists, guild, oc, verify

mod = Blueprint("botroutes", __name__)

# Guild Routes
mod.add_url_rule("/bot/dashboard", view_func=guild.dashboard, methods=["GET"])
mod.add_url_rule(
    "/bot/dashboard/<string:guildid>",
    view_func=guild.guild_dashboard,
    methods=["GET"],
)

# Assist Routes
mod.add_url_rule(
    "/bot/assists/<string:guildid>/update",
    view_func=assists.assists_update,
    methods=["GET", "POST"],
)

# Verify Routes
mod.add_url_rule(
    "/bot/dashboard/<string:guildid>/verify",
    view_func=verify.verify_dashboard,
    methods=["GET"],
)

# OC Routes
mod.add_url_rule(
    "/bot/dashboard/<string:guildid>/oc",
    view_func=oc.oc_dashboard,
    methods=["GET"],
)


@mod.route("/bot")
def index():
    return render_template("bot/index.html")
