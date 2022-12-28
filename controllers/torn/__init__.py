# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import Blueprint, render_template

from controllers.torn import factions, users

mod = Blueprint("tornroutes", __name__)

# Factions Routes
mod.add_url_rule("/torn/faction/<int:tid>", view_func=factions.faction_data, methods=["GET"])
mod.add_url_rule(
    "/torn/faction/members/<int:tid>",
    view_func=factions.faction_members_data,
    methods=["GET"],
)
mod.add_url_rule("/torn/factions", view_func=factions.factions, methods=["GET"])
mod.add_url_rule("/torn/factionsdata", view_func=factions.factions_data, methods=["GET"])

# Users Routes
mod.add_url_rule("/torn/user/<int:tid>", view_func=users.user_data, methods=["GET"])
mod.add_url_rule("/torn/users", view_func=users.users, methods=["GET"])
mod.add_url_rule("/torn/usersdata", view_func=users.users_data, methods=["GET"])


@mod.route("/torn")
def index():
    return render_template("torn/index.html")
