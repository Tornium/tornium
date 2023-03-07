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
from flask_login import login_required

from controllers.bot import assists, guild, oc, stakeout, verify

mod = Blueprint("botroutes", __name__)

# Guild Routes
mod.add_url_rule("/bot/dashboard", view_func=guild.dashboard, methods=["GET"])
mod.add_url_rule(
    "/bot/dashboard/<string:guildid>",
    view_func=guild.guild_dashboard,
    methods=["GET", "POST"],
)
mod.add_url_rule(
    "/bot/dashboard/<string:guildid>/<int:factiontid>",
    view_func=guild.update_guild,
    methods=["POST"],
)

# Stakeout Routes
mod.add_url_rule(
    "/bot/stakeouts/<string:guildid>",
    view_func=stakeout.stakeouts_dashboard,
    methods=["GET", "POST"],
)
mod.add_url_rule(
    "/bot/stakeouts/<string:guildid>/<int:stype>",
    view_func=stakeout.stakeouts,
    methods=["GET"],
)
mod.add_url_rule(
    "/bot/stakeouts/<string:guildid>/modal",
    view_func=stakeout.stakeout_data,
    methods=["GET"],
)
mod.add_url_rule(
    "/bot/stakeouts/<string:guildid>/update",
    view_func=stakeout.stakeout_update,
    methods=["GET", "POST"],
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
