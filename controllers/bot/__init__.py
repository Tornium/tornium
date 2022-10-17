# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import Blueprint, render_template
from flask_login import login_required

from controllers.bot import assists
from controllers.bot import guild
from controllers.bot import stakeout
from controllers.bot import verify

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


@mod.route("/bot")
def index():
    return render_template("bot/index.html")


@mod.route("/bot/documentation")
@login_required
def documentation():
    return render_template("bot/documentation.html")


@mod.route("/bot/host")
@login_required
def hosting():
    return render_template("bot/host.html")
