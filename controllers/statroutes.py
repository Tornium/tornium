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

from flask import Blueprint, render_template, request
from flask_login import current_user, fresh_login_required, login_required
from mongoengine.queryset.visitor import Q
from tornium_commons.formatters import bs_to_range, commas, get_tid, rel_time
from tornium_commons.models import FactionModel, StatModel, UserModel

from controllers.faction.decorators import aa_required

mod = Blueprint("statroutes", __name__)


@mod.route("/stats")
def index():
    return render_template("stats/index.html")


@mod.route("/stats/db")
def stats():
    if current_user.is_authenticated and current_user.key != "":
        return render_template("stats/db.html", battlescore=current_user.battlescore, key=current_user.key)
    else:
        return render_template("stats/db.html", battlescore=-1, key=-1)


@mod.route("/stats/dbdata")
def stats_data():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    search_value = request.args.get("search[value]")
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")
    min_bs = request.args.get("minBS")
    max_bs = request.args.get("maxBS")

    stats = []

    if current_user.is_authenticated:
        if get_tid(search_value):
            stat_entries = StatModel.objects(
                Q(tid=get_tid(search_value))
                & (Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid))
            )
        else:
            stat_entries = StatModel.objects(
                Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid)
            )
    else:
        if get_tid(search_value):
            stat_entries = StatModel.objects(Q(tid=get_tid(search_value)) & Q(globalstat=True))
        else:
            stat_entries = StatModel.objects(globalstat=True)

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

    stat_entry: StatModel
    for stat_entry in stat_entries_subset:
        if stat_entry.tid in users:
            user: UserModel = users[stat_entry.tid]
        else:
            user: UserModel = UserModel.objects(_id=stat_entry.tid).first()
            users[stat_entry.tid] = user

        stats.append(
            [
                stat_entry.tid if user is None else f"{user.name} [{user.tid}]",
                commas(int(sum(bs_to_range(stat_entry.battlescore)) / 2)),
                rel_time(datetime.datetime.fromtimestamp(stat_entry.timeadded)),
            ]
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": StatModel.objects.count(),
        "recordsFiltered": StatModel.objects.count(),
        "data": stats,
    }

    return data


@mod.route("/stats/chain")
@login_required
def chain():
    return render_template("stats/chain.html")


@mod.route("/stats/config", methods=["GET", "POST"])
@fresh_login_required
@aa_required
def config():
    faction_model = FactionModel.objects(tid=current_user.factiontid).first()

    if request.method == "POST":
        if (request.form.get("enabled") is not None) ^ (request.form.get("disabled") is not None):
            if request.form.get("enabled") is not None:
                faction_model.statconfig["global"] = 1
            else:
                faction_model.statconfig["global"] = 0

            faction_model.save()

    return render_template("stats/config.html", config=faction_model.statconfig)
