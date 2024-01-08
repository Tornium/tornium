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

from controllers.faction import assists, banking, bot, chain, crimes, members

mod = Blueprint("factionroutes", __name__)

# Assist Routes
mod.add_url_rule("/faction/assists/<string:guid>", view_func=assists.assist_forward, methods=["GET"])

# Banking Routes
mod.add_url_rule("/faction/bankingaa", view_func=banking.banking_aa, methods=["GET"])
mod.add_url_rule("/faction/bankingdata", view_func=banking.banking_data, methods=["GET"])
mod.add_url_rule("/faction/banking", view_func=banking.banking, methods=["GET"])
mod.add_url_rule("/faction/banking/fulfill/<guid>", view_func=banking.fulfill, methods=["GET"])
mod.add_url_rule("/faction/userbankingdata", view_func=banking.user_banking_data, methods=["GET"])

# Bot Routes
mod.add_url_rule("/faction/bot", view_func=bot.bot, methods=["GET", "POST"])

# Chain Routes
mod.add_url_rule("/faction/chain", view_func=chain.chain, methods=["GET"])

# Member Routes
mod.add_url_rule("/faction/members", view_func=members.members, methods=["GET"])

# Crime Routes
mod.add_url_rule("/faction/crimes", view_func=crimes.crimes_dashboard, methods=["GET"])


@mod.route("/faction")
def index():
    return render_template("faction/index.html")
