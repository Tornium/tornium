# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import Blueprint, render_template, send_from_directory, request
from flask_login import login_required

from controllers.decorators import *

mod = Blueprint("baseroutes", __name__)


@mod.route("/")
@mod.route("/index")
def index():
    return render_template("index.html")


@mod.route("/robots.txt")
@mod.route("/toast.js")
@mod.route("/favicon.svg")
@mod.route("/login.css")
@mod.route("/utils.js")
@mod.route("/bot/stakeouts.js")
@mod.route("/bot/guild.js")
@mod.route("/faction/armory.js")
@mod.route("/faction/banking.js")
@mod.route("/faction/bankingaa.js")
@mod.route("/faction/group.js")
@mod.route("/faction/members.js")
@mod.route("/stats/db.js")
@mod.route("/stats/list.js")
@mod.route("/torn/factions.js")
@mod.route("/torn/users.js")
def static():
    return send_from_directory("static", request.path[1:])


@mod.route("/astats/db.js")
@mod.route("/faction/recruitment.js")
@mod.route("/faction/schedule.js")
@mod.route("/faction/schedulechart.js")
@login_required
@pro_required
def static_pro():
    return send_from_directory("static", request.path[1:])


@mod.route("/admin/database/faction.js")
@mod.route("/admin/database/server.js")
@mod.route("/admin/database/user.js")
@login_required
@admin_required
def static_admin():
    return send_from_directory("static", request.path[1:])
