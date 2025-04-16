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

from flask import Blueprint

from controllers.api.v1 import (
    bot,
    faction,
    gateway,
    items,
    key,
    notification,
    stat,
    stocks,
    user,
)

mod = Blueprint("api_routes_v1", __name__)


# /api/v1/key
mod.add_url_rule("/api/v1/key", view_func=key.set_key, methods=["POST"])
mod.add_url_rule("/api/v1/key/<guid>", view_func=key.toggle_key, methods=["PATCH"])
mod.add_url_rule("/api/v1/key/<guid>", view_func=key.delete_key, methods=["DELETE"])

# /api/v1/gateway
mod.add_url_rule("/api/v1/gateway", view_func=gateway.create_gateway_client, methods=["POST"])
mod.add_url_rule("/api/v1/gateway/<client_id>", view_func=gateway.get_gateway_client, methods=["GET"])

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
    "/api/v1/bot/<int:guild_id>/attacks/retal/<int:faction_tid>/channel",
    view_func=bot.attacks.faction_retal_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/attacks/retal/<int:faction_tid>/roles",
    view_func=bot.attacks.faction_retal_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/attacks/chain-bonus/<int:faction_tid>/channel",
    view_func=bot.attacks.faction_chain_bonus_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/attacks/chain-bonus/<int:faction_tid>/roles",
    view_func=bot.attacks.faction_chain_bonus_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/attacks/chain-bonus/<int:faction_tid>/length",
    view_func=bot.attacks.faction_chain_bonus_length,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/attacks/chain-alert/<int:faction_tid>/channel",
    view_func=bot.attacks.faction_chain_alert_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/attacks/chain-alert/<int:faction_tid>/roles",
    view_func=bot.attacks.faction_chain_alert_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/tool/channel",
    view_func=bot.crimes.set_tool_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/tool/roles",
    view_func=bot.crimes.set_tool_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/tool/crimes",
    view_func=bot.crimes.set_tool_crimes,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/range/channel",
    view_func=bot.crimes.set_extra_range_channel,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/range/roles",
    view_func=bot.crimes.set_extra_range_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/range/minimum",
    view_func=bot.crimes.set_extra_range_global_minimum,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/range/maximum",
    view_func=bot.crimes.set_extra_range_global_maximum,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/range/local/<oc_name>",
    view_func=bot.crimes.create_extra_range_local,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/range/local/<oc_name>",
    view_func=bot.crimes.delete_extra_range_local,
    methods=["DELETE"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/crimes/<int:faction_tid>/range/local/<oc_name>",
    view_func=bot.crimes.patch_extra_range_local,
    methods=["PATCH"],
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
    "/api/v1/bot/<int:guild_id>/notification",
    view_func=bot.notification.get_notification_config,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/notification",
    view_func=bot.notification.toggle_notifications,
    methods=["PUT"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/notification/log-channel",
    view_func=bot.notification.set_notifications_log_channel,
    methods=["PUT"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/notifications",
    view_func=bot.notification.get_server_notifications,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/verify/jail",
    view_func=bot.verify.guild_gateway_verification,
    methods=["POST", "DELETE"],
)
mod.add_url_rule(
    "/api/v1/bot/<int:guild_id>/verify/jail/channel",
    view_func=bot.verify.guild_jail_channel,
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
    "/api/v1/bot/verify/auto",
    view_func=bot.verify.guild_auto_verification,
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
mod.add_url_rule(
    "/api/v1/bot/verify/log",
    view_func=bot.verify.guild_verification_log,
    methods=["POST"],
)
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
mod.add_url_rule(
    "/api/v1/faction/banking",
    view_func=faction.banking.banking_request,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/faction/banking/vault",
    view_func=faction.banking.vault_balance,
    methods=["GET"],
)
mod.add_url_rule("/api/v1/faction/chain", view_func=faction.chain.chain_config, methods=["GET"])
mod.add_url_rule("/api/v1/faction/crimes/names", view_func=faction.crimes.get_oc_names, methods=["GET"])
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

# /api/v1/stat
mod.add_url_rule("/api/v1/chain-list", view_func=stat.generate_chain_list, methods=["GET"])
mod.add_url_rule("/api/v1/stat/<int:tid>", view_func=stat.get_stat_user, methods=["GET"])

# /api/v1/stocks
mod.add_url_rule("/api/v1/stocks", view_func=stocks.data.stocks_data, methods=["GET"])
mod.add_url_rule("/api/v1/stocks/benefits", view_func=stocks.data.stock_benefits, methods=["GET"])
mod.add_url_rule("/api/v1/stocks/movers", view_func=stocks.movers.stock_movers, methods=["GET"])

# /api/v1/user
mod.add_url_rule("/api/v1/user", view_func=user.get_user, methods=["GET"])
mod.add_url_rule("/api/v1/user/guilds", view_func=user.get_admin_guilds, methods=["GET"])
mod.add_url_rule("/api/v1/user/<int:tid>", view_func=user.get_specific_user, methods=["GET"])
mod.add_url_rule(
    "/api/v1/user/estimate/<int:tid>",
    view_func=user.estimate_specific_user,
    methods=["GET"],
)
mod.add_url_rule("/api/v1/user/<int:tid>/stat", view_func=user.latest_user_stats, methods=["GET"])

# /api/v1/notification
mod.add_url_rule("/api/v1/notification/trigger", view_func=notification.trigger.list_triggers, methods=["GET"])
mod.add_url_rule("/api/v1/notification/trigger", view_func=notification.trigger.create_trigger, methods=["POST"])
mod.add_url_rule(
    "/api/v1/notification/trigger/<trigger_id>", view_func=notification.trigger.create_trigger, methods=["PUT"]
)
mod.add_url_rule(
    "/api/v1/notification/trigger/<trigger_id>/guild/<int:guild_id>",
    view_func=notification.trigger.setup_trigger_guild,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/v1/notification/<notification_id>",
    view_func=notification.notification.update_guild_notification,
    methods=["PUT"],
)
mod.add_url_rule(
    "/api/v1/notification/<notification_id>",
    view_func=notification.notification.delete_guild_notification,
    methods=["DElETE"],
)
mod.add_url_rule(
    "/api/v1/notification/<notification_id>/toggle",
    view_func=notification.notification.toggle_guild_notification,
    methods=["POST"],
)
