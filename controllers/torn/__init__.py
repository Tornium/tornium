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

from controllers.torn import factions, stocks, users

mod = Blueprint("tornroutes", __name__)

# Factions Routes
mod.add_url_rule("/torn/faction/<int:tid>", view_func=factions.faction_data, methods=["GET"])
mod.add_url_rule(
    "/torn/faction/members/<int:tid>",
    view_func=factions.faction_members_data,
    methods=["GET"],
)
mod.add_url_rule("/torn/factions", view_func=factions.factions, methods=["GET"])
mod.add_url_rule("/torn/factions/member-report", view_func=factions.faction_members_report, methods=["GET"])
mod.add_url_rule("/torn/factions/member-report/<string:rid>", view_func=factions.view_member_report, methods=["GET"])
mod.add_url_rule("/torn/factionsdata", view_func=factions.factions_data, methods=["GET"])

# Stock Routes
mod.add_url_rule("/torn/stocks", view_func=stocks.stocks, methods=["GET"])

# Users Routes
mod.add_url_rule("/torn/user/<int:tid>", view_func=users.user_data, methods=["GET"])
mod.add_url_rule("/torn/users", view_func=users.users, methods=["GET"])
mod.add_url_rule("/torn/usersdata", view_func=users.users_data, methods=["GET"])
mod.add_url_rule("/torn/userspsdata", view_func=users.users_ps_data, methods=["GET"])


@mod.route("/torn")
def index():
    return render_template("torn/index.html")
