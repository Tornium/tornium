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

import datetime
import math

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from mongoengine.queryset.visitor import Q

import utils
from controllers.faction.decorators import aa_required
from models.faction import Faction
from models.factionmodel import FactionModel
from models.statmodel import StatModel
from models.user import User
from models.usermodel import UserModel

mod = Blueprint("statroutes", __name__)


@mod.route("/stats")
def index():
    return render_template("stats/index.html")


@mod.route("/stats/db")
@login_required
def stats():
    return render_template("stats/db.html", battlescore=current_user.battlescore, key=current_user.key)


@mod.route("/stats/dbdata")
@login_required
def stats_data():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    search_value = request.args.get("search[value]")
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")
    min_bs = request.args.get("minBS")
    max_bs = request.args.get("maxBS")

    stats = []

    if utils.get_tid(search_value):
        stat_entries = StatModel.objects(
            Q(tid__startswith=utils.get_tid(search_value))
            & (Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid))
        )
    else:
        stat_entries = StatModel.objects(
            Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid)
        )

    if min_bs != "" and max_bs != "":
        stat_entries = stat_entries.filter(Q(battlescore__gt=int(min_bs)) & Q(battlescore__lt=int(max_bs)))
    elif min_bs == "" and max_bs != "":
        stat_entries = stat_entries.filter(battlescore__lt=int(max_bs))
    elif min_bs != "" and max_bs == "":
        stat_entries = stat_entries.filter(battlescore__gt=int(min_bs))

    if ordering_direction == "asc":
        ordering_direction = "+"
    else:
        ordering_direction = "-"

    if ordering == 0:
        stat_entries = stat_entries.order_by(f"{ordering_direction}tid")
    elif ordering == 1:
        stat_entries = stat_entries.order_by(f"{ordering_direction}battlescore")
    else:
        stat_entries = stat_entries.order_by(f"{ordering_direction}timeadded")

    stat_entries_subset = stat_entries[start : start + length]
    users = {}

    for stat_entry in stat_entries_subset:
        if stat_entry.tid in users:
            user: UserModel = users[stat_entry.tid]
        else:
            user: UserModel = UserModel.objects(_id=stat_entry.tid).first()
            users[stat_entry.tid] = user

        stats.append(
            [
                stat_entry.tid if user is None else f"{user.name} [{user.tid}]",
                utils.commas(int(stat_entry.battlescore)),
                utils.rel_time(datetime.datetime.fromtimestamp(stat_entry.timeadded)),
            ]
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": StatModel.objects.count(),
        "recordsFiltered": StatModel.objects.count(),
        "data": stats,
    }

    return data


@mod.route("/stats/userdata")
@login_required
def user_data():
    tid = int(utils.get_tid(request.args.get("user")))
    stats = []
    stat_entries = StatModel.objects(
        Q(tid=tid) & (Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid))
    )

    factions = {}
    users = {}

    for stat_entry in stat_entries:
        if stat_entry.tid != tid:
            continue

        if str(stat_entry.addedid) in users:
            user = users[str(stat_entry.addedid)]
        else:
            user = UserModel.objects(tid=stat_entry.addedid).first()
            users[str(stat_entry.addedid)] = user

        if str(stat_entry.addedfactiontid) in factions:
            faction = factions[str(stat_entry.addedfactiontid)]
        else:
            faction = FactionModel.objects(tid=stat_entry.addedfactiontid).first()
            factions[str(stat_entry.addedfactiontid)] = faction

        stats.append(
            {
                "statid": stat_entry.id,
                "tid": stat_entry.tid,
                "battlescore": stat_entry.battlescore,
                "timeadded": stat_entry.timeadded,
                "added_user": user,
                "added_faction": faction,
                "added_faction_tid": stat_entry.addedfactiontid,
                "globalstat": stat_entry.globalstat,
            }
        )

    user = User(tid=tid)

    # If user's last action was over a month ago and last refresh was over a week ago
    if utils.now() - user.last_action > 30 * 24 * 60 * 60 and utils.now() - user.last_refresh > 604800:
        user.refresh(key=current_user.key)
    elif utils.now() - user.last_action <= 30 * 24 * 60 * 60:
        user.refresh(key=current_user.key)

    if user.factiontid != 0:
        faction = Faction(tid=user.factiontid)
    else:
        faction = None

    ff = 1 + (8 / 3 * stats[-1]["battlescore"] / current_user.battlescore)
    ff = ff if ff <= 3 else 3
    respect = (math.log(user.level) + 1) / 4 * ff

    return render_template(
        "stats/statmodal.html",
        user=user,
        faction=faction,
        stats=stats,
        ff=round(ff, 2),
        respect=round(respect, 2),
    )


@mod.route("/stats/chain")
@login_required
def chain():
    return render_template("stats/chain.html", key=current_user.key)


@mod.route("/stats/config", methods=["GET", "POST"])
@login_required
@aa_required
def config():
    faction = Faction(current_user.factiontid)

    if request.method == "POST":
        faction_model = FactionModel.objects(tid=current_user.factiontid).first()

        if (request.form.get("enabled") is not None) ^ (request.form.get("disabled") is not None):
            if request.form.get("enabled") is not None:
                faction_model.statconfig["global"] = 1
            else:
                faction_model.statconfig["global"] = 0

            faction_model.save()

    return render_template("stats/config.html", config=faction.stat_config)
