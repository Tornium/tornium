# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import Blueprint, render_template

from controllers.api import astat
from controllers.api import bot
from controllers.api import faction
from controllers.api import key
from controllers.api import stakeout
from controllers.api import stat
from controllers.api import user

mod = Blueprint("apiroutes", __name__)


# /api/key
mod.add_url_rule("/api/key", view_func=key.test_key, methods=["GET"])
mod.add_url_rule("/api/key", view_func=key.create_key, methods=["POST"])
mod.add_url_rule("/api/key", view_func=key.remove_key, methods=["DELETE"])

# /api/bot
mod.add_url_rule(
    "/api/bot/retal/faction/channel",
    view_func=bot.retal.faction_retal_channel,
    methods=["POST"],
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
    "/api/bot/verify/faction/roles",
    view_func=bot.verify.faction_roles,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/bot/verify/log", view_func=bot.verify.guild_verification_log, methods=["POST"]
)
mod.add_url_rule(
    "/api/bot/verify/roles",
    view_func=bot.verify.guild_verification_roles,
    methods=["POST"],
)

# /api/faction
mod.add_url_rule(
    "/api/faction/assist", view_func=faction.assist.forward_assist, methods=["POST"]
)
mod.add_url_rule(
    "/api/faction/banking", view_func=faction.banking.banking_request, methods=["POST"]
)
mod.add_url_rule(
    "/api/faction/banking/vault", view_func=faction.banking.vault_balance, methods=["GET"]
)
mod.add_url_rule("/api/faction/group", view_func=faction.group.group_modify, methods=["POST"])
mod.add_url_rule(
    "/api/faction/positions",
    view_func=faction.positions.get_positions,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/faction/recruitment/message",
    view_func=faction.recruitment.message_send,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/faction/recruitment/recruit",
    view_func=faction.recruitment.invite_recruit,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/faction/recruitment/recruit",
    view_func=faction.recruitment.remove_recruit,
    methods=["DELETE"],
)
mod.add_url_rule(
    "/api/faction/recruitment/recruiter",
    view_func=faction.recruitment.remove_recruiter,
    methods=["DELETE"],
)
mod.add_url_rule(
    "/api/faction/recruitment/recruiter",
    view_func=faction.recruitment.add_recruiter,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/faction/recruitment/recruiter/code",
    view_func=faction.recruitment.refresh_code,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/faction/schedule", view_func=faction.schedule.create_schedule, methods=["POST"]
)
mod.add_url_rule(
    "/api/faction/schedule", view_func=faction.schedule.delete_schedule, methods=["DELETE"]
)
mod.add_url_rule(
    "/api/faction/schedule/setup", view_func=faction.schedule.schedule_setup, methods=["POST"]
)
mod.add_url_rule(
    "/api/faction/schedule/watcher/<string:uuid>",
    view_func=faction.schedule.get_schedule,
    methods=["GET"],
)
mod.add_url_rule(
    "/api/faction/schedule/watcher",
    view_func=faction.schedule.add_chain_watcher,
    methods=["POST"],
)
mod.add_url_rule(
    "/api/faction/schedule/watcher",
    view_func=faction.schedule.remove_chain_watcher,
    methods=["DELETE"],
)
mod.add_url_rule(
    "/api/faction/schedule/activity",
    view_func=faction.schedule.add_chain_availability,
    methods=["POST"],
)

# /api/stakeout
mod.add_url_rule(
    "/api/stakeout/<string:stype>", view_func=stakeout.create_stakeout, methods=["POST"]
)

# /api/stat
mod.add_url_rule("/api/stat", view_func=stat.generate_chain_list, methods=["GET"])
mod.add_url_rule("/api/stat/<int:tid>", view_func=stat.get_stat_user, methods=["GET"])

# /api/astat
mod.add_url_rule(
    "/api/astat/attack/started", view_func=astat.attack_start, methods=["POST"]
)
mod.add_url_rule(
    "/api/astat/attack/finished", view_func=astat.attack_end, methods=["POST"]
)
mod.add_url_rule(
    "/api/astat/stats/<logID>", view_func=astat.attack_log_stats, methods=["GET"]
)

# /api/user
mod.add_url_rule("/api/user", view_func=user.get_user, methods=["GET"])


@mod.route("/api")
def index():
    return render_template("api/index.html")
