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

from controllers.api import bot, faction, key, stakeout, stat, user

mod = Blueprint("apiroutes", __name__)


# /api/key
mod.add_url_rule("/api/key", view_func=key.test_key, methods=["GET"])
mod.add_url_rule("/api/key", view_func=key.create_key, methods=["POST"])
mod.add_url_rule("/api/key", view_func=key.remove_key, methods=["DELETE"])

# /api/bot
mod.add_url_rule(
    "/api/bot/<int:guildid>/assists/channel",
    view_func=bot.assists.assists_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/bot/<int:guildid>/faction/<int:factiontid>/oc/<string:notif>/<string:element>",
    view_func=bot.oc.oc_config_setter,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/bot/retal/faction/channel",
    view_func=bot.retal.faction_retal_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/bot/server/<int:guildid>",
    view_func=bot.config.server_config,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/bot/server/<int:guildid>/channels",
    view_func=bot.utils.get_channels,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/bot/server/<int:guildid>/roles",
    view_func=bot.utils.get_roles,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/bot/verify/<int:guildid>",
    view_func=bot.verify.verification_config,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/bot/verify",
    view_func=bot.verify.guild_verification,
    methods=["POST", "DELETE"],
)
mod.add_url_rule(
    "/api/bot/verify/faction",
    view_func=bot.verify.faction_verification,
    methods=["POST", "DELETE"],
)
mod.add_url_rule(
    "/api/bot/verify/faction/<int:factiontid>/position/<string:position>",
    view_func=bot.verify.faction_position_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/bot/verify/faction/<int:factiontid>/roles",
    view_func=bot.verify.faction_roles,
    methods=["POST"],
)
mod.add_url_rule("/api/bot/verify/log", view_func=bot.verify.guild_verification_log, methods=["POST"])
mod.add_url_rule(
    "/api/bot/verify/roles",
    view_func=bot.verify.guild_verification_roles,
    methods=["POST"],
)

# /api/faction
mod.add_url_rule("/api/faction/assist", view_func=faction.assist.forward_assist, methods=["POST"])
mod.add_url_rule("/api/faction/banking", view_func=faction.banking.banking_request, methods=["POST"])
mod.add_url_rule(
    "/api/faction/banking/vault",
    view_func=faction.banking.vault_balance,
    methods=["GET"],
)
mod.add_url_rule("/api/faction/chain", view_func=faction.chain.chain_config, methods=["GET"])
mod.add_url_rule(
    "/api/faction/chain/od/channel",
    view_func=faction.chain.chain_od_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/faction/positions",
    view_func=faction.positions.get_positions,
    methods=["GET"],
)

# /api/stakeout
mod.add_url_rule("/api/stakeout/<string:stype>", view_func=stakeout.create_stakeout, methods=["POST"])

# /api/stat
mod.add_url_rule("/api/stat", view_func=stat.generate_chain_list, methods=["GET"])
mod.add_url_rule("/api/stat/<int:tid>", view_func=stat.get_stat_user, methods=["GET"])

# /api/user
mod.add_url_rule("/api/user", view_func=user.get_user, methods=["GET"])


@mod.route("/api")
def index():
    return render_template("api/index.html")
