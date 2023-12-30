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

from flask import Blueprint

from controllers.api import bot, faction, items, key, report, stat, stocks, user

mod = Blueprint("api_routes_v1", __name__)


# /api/v1/key
mod.add_url_rule("/api/v1/key", view_func=key.test_key, methods=["GET"])
mod.add_url_rule("/api/v1/key", view_func=key.set_key, methods=["POST"])
mod.add_url_rule("/api/v1/token", view_func=key.test_token, methods=["GET"])

# /api/v1/bot
mod.add_url_rule(
    "/api/v1/bot/<int:guildid>/armory",
    view_func=bot.armory.armory_toggle,
    methods=["PUT"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/armory/<int:faction_tid>",
    view_func=bot.armory.armory_faction_toggle,
    methods=["PUT"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guildid>/armory/<int:factionid>/channel",
    view_func=bot.armory.armory_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guildid>/armory/<int:factionid>/item",
    view_func=bot.armory.armory_tracked_items,
    methods=["DELETE", "POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guildid>/armory/<int:factionid>/roles",
    view_func=bot.armory.armorer_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guildid>/assists/channel",
    view_func=bot.assists.assists_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/assists/roles/<string:role_type>",
    view_func=bot.assists.assists_role_set,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/faction",
    view_func=bot.faction.faction_setter,
    methods=["DELETE", "POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/faction/<int:faction_tid>/banking",
    view_func=bot.banking.banking_setter,
    methods=["GET", "POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/faction/<int:faction_tid>/oc/<string:notif>/<string:element>",
    view_func=bot.oc.oc_config_setter,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/stocks/feed",
    view_func=bot.stocks.stocks_feed_options,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/stocks/feed/channel",
    view_func=bot.stocks.stocks_feed_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/retal/faction/channel",
    view_func=bot.retal.faction_retal_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/retal/faction/roles",
    view_func=bot.retal.faction_retal_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/server/<int:guild_id>",
    view_func=bot.config.server_config,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/v1/bot/server/<int:guild_id>/channels",
    view_func=bot.utils.get_channels,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/v1/bot/server/<int:guild_id>/roles",
    view_func=bot.utils.get_roles,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/v1/bot/verify/<int:guild_id>",
    view_func=bot.verify.verification_config,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/v1/bot/verify",
    view_func=bot.verify.guild_verification,
    methods=["POST", "DELETE"],
)
mod.add_url_rule(
    "/api/v1/bot/verify/faction",
    view_func=bot.verify.faction_verification,
    methods=["POST", "DELETE"],
)
mod.add_url_rule(
    "/api/v1/bot/verify/faction/<int:faction_tid>/position/<string:position>",
    view_func=bot.verify.faction_position_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/verify/faction/<int:faction_tid>/roles",
    view_func=bot.verify.faction_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/verify/exclusion",
    view_func=bot.verify.guild_exclusion_roles,
    methods=["POST"],
)
mod.add_url_rule("/api/v1/bot/verify/log", view_func=bot.verify.guild_verification_log, methods=["POST"])
mod.add_url_rule(
    "/api/v1/bot/verify/roles",
    view_func=bot.verify.guild_verification_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/verify/template",
    view_func=bot.verify.guild_verification_template,
    methods=["POST"],
)

# /api/v1/faction
mod.add_url_rule("/api/v1/faction/assist", view_func=faction.assist.forward_assist, methods=["POST"])
mod.add_url_rule("/api/v1/faction/assists", view_func=faction.assist.valid_assists, methods=["GET"])
mod.add_url_rule("/api/v1/faction/banking", view_func=faction.banking.banking_request, methods=["POST"])
mod.add_url_rule(
    "/api/v1/faction/banking/vault",
    view_func=faction.banking.vault_balance,
    methods=["GET"],
)
mod.add_url_rule("/api/v1/faction/chain", view_func=faction.chain.chain_config, methods=["GET"])
mod.add_url_rule(
    "/api/v1/faction/chain/od/channel",
    view_func=faction.chain.chain_od_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/faction/positions",
    view_func=faction.positions.get_positions,
    methods=["GET"],
)

# /api/v1/items
mod.add_url_rule("/api/v1/items", view_func=items.item_name_map, methods=["GET"])

# /api/v1/report
mod.add_url_rule(
    "/api/v1/report/faction/members",
    view_func=report.faction_member.get_reports,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/v1/report/faction/members",
    view_func=report.faction_member.create_report,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/report/faction/members/<string:rid>",
    view_func=report.faction_member.delete_report,
    methods=["DELETE"],
)
mod.add_url_rule(
    "/api/v1/report/faction/members/<string:rid>",
    view_func=report.faction_member.get_report,
    methods=["GET"],
)

# /api/v1/stat
mod.add_url_rule("/api/v1/stat", view_func=stat.generate_chain_list, methods=["GET"])
mod.add_url_rule("/api/v1/stat/<int:tid>", view_func=stat.get_stat_user, methods=["GET"])

# /api/v1/stocks
mod.add_url_rule("/api/v1/stocks", view_func=stocks.data.stocks_data, methods=["GET"])
mod.add_url_rule("/api/v1/stocks/benefits", view_func=stocks.data.stock_benefits, methods=["GET"])
mod.add_url_rule("/api/v1/stocks/movers", view_func=stocks.movers.stock_movers, methods=["GET"])

# /api/v1/user
mod.add_url_rule("/api/v1/user", view_func=user.get_user, methods=["GET"])
mod.add_url_rule("/api/v1/user/<int:tid>", view_func=user.get_specific_user, methods=["GET"])
mod.add_url_rule(
    "/api/v1/user/estimate/<int:tid>",
    view_func=user.estimate_specific_user,
    methods=["GET"],
)
