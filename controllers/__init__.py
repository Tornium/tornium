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


@mod.route("/static/robots.txt")
@mod.route("/static/toast.js")
@mod.route("/static/favicon.svg")
@mod.route("/static/login.css")
@mod.route("/static/utils.js")
@mod.route("/static/bot/stakeouts.js")
@mod.route("/static/bot/guild.js")
@mod.route("/static/bot/verify.js")
@mod.route("/static/faction/armory.js")
@mod.route("/static/faction/banking.js")
@mod.route("/static/faction/bankingaa.js")
@mod.route("/static/faction/members.js")
@mod.route("/static/stats/db.js")
@mod.route("/static/stats/list.js")
@mod.route("/static/torn/factions.js")
@mod.route("/static/torn/users.js")
def static():
    return send_from_directory("static", request.path[8:])


@mod.route("/userscripts/tornium-assists.user.js")
def userscripts():
    return send_from_directory("static", request.path[1:])


@mod.route("/static/astats/db.js")
@mod.route("/static/faction/recruitment.js")
@login_required
@pro_required
def static_pro():
    return send_from_directory("static", request.path[1:])


@mod.route("/static/admin/database/faction.js")
@mod.route("/static/admin/database/server.js")
@mod.route("/static/admin/database/user.js")
@login_required
@admin_required
def static_admin():
    return send_from_directory("static", request.path[1:])
