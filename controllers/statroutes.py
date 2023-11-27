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

import typing

from flask import Blueprint, render_template, request
from flask_login import current_user, fresh_login_required, login_required
from peewee import DoesNotExist
from tornium_commons import rds
from tornium_commons.formatters import bs_to_range, commas, get_tid, rel_time
from tornium_commons.models import Faction, Stat, User

import utils
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

    stat_entries: typing.Iterable[Stat]
    if current_user.is_authenticated and current_user.faction_id not in (None, 0):
        if get_tid(search_value):
            stat_entries = Stat.select().where(
                (Stat.tid == get_tid(search_value))
                & ((Stat.added_group == 0) | (Stat.added_group == current_user.faction.tid))
            )
        else:
            stat_entries = Stat.select().where((Stat.added_group == 0) | (Stat.added_group == current_user.faction_id))
    else:
        if get_tid(search_value):
            stat_entries = Stat.select().where((Stat.tid == get_tid(search_value)) & (Stat.added_group == 0))
        else:
            stat_entries = Stat.select().where(Stat.added_group == 0)

    if min_bs != "" and max_bs != "":
        stat_entries = stat_entries.where((Stat.battlescore >= int(min_bs)) & (Stat.battlescore <= int(max_bs)))
    elif min_bs == "" and max_bs != "":
        stat_entries = stat_entries.where(Stat.battlescore <= int(max_bs))
    elif min_bs != "" and max_bs == "":
        stat_entries = stat_entries.where(Stat.battlescore >= int(min_bs))

    if ordering == 0:
        stat_entries = stat_entries.order_by(utils.table_order(ordering_direction, Stat.tid))
    elif ordering == 1:
        stat_entries = stat_entries.order_by(utils.table_order(ordering_direction, Stat.battlescore))
    else:
        stat_entries = stat_entries.order_by(utils.table_order(ordering_direction, Stat.time_added))

    # TODO: pagination doesn't work when the page is first loaded
    # Shows the same data every time
    stat_entries_subset = stat_entries.paginate(start // length, length)
    stat_entries_subset.join(User)

    stats = [
        [
            stat_entry.tid_id if stat_entry.tid is None else f"{stat_entry.tid.name} [{stat_entry.tid_id}]",
            commas(int(sum(bs_to_range(stat_entry.battlescore)) / 2)),
            rel_time(stat_entry.time_added),
        ]
        for stat_entry in stat_entries_subset
    ]

    return {
        "draw": request.args.get("draw"),
        "recordsTotal": Stat.select().count(),
        "recordsFiltered": stat_entries.select().count(),
        "data": stats,
    }, 200


@mod.route("/stats/chain")
@login_required
def chain():
    return render_template("stats/chain.html")


@mod.route("/stats/config", methods=["GET", "POST"])
@fresh_login_required
@aa_required
def config():
    stats_global = current_user.faction.stats_db_global

    if request.method == "POST":
        if (request.form.get("enabled") is not None) ^ (request.form.get("disabled") is not None):
            if request.form.get("enabled") is not None:
                stats_global = True
            else:
                stats_global = False

            Faction.update(stats_db_global=stats_global).where(Faction.tid == current_user.faction_id).execute()

    return render_template("stats/config.html", stats_global=stats_global)
