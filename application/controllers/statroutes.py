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

import csv
import datetime
import io
import typing
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import (
    Blueprint,
    Response,
    abort,
    render_template,
    request,
    stream_with_context,
)
from flask_login import current_user, login_required
from peewee import DoesNotExist
from tornium_celery.tasks.api import tornget
from tornium_commons.db_connection import db
from tornium_commons.formatters import bs_to_range, commas, get_tid, rel_time
from tornium_commons.models import Faction, Stat, User

import utils
from controllers.faction.decorators import aa_required
from estimate import estimate_user

mod = Blueprint("statroutes", __name__)


@mod.route("/stats")
def index():
    return render_template("stats/index.html")


@mod.route("/stats/db")
def stats():
    if current_user.is_authenticated and current_user.key is not None:
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
                & ((Stat.added_group == 0) | (Stat.added_group == current_user.faction_id))
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

    stat_entries_subset = stat_entries.paginate(start // length + 1, length)
    stat_entries_subset.join(User)

    stats = [
        [
            (stat_entry.tid_id if stat_entry.tid is None else f"{stat_entry.tid.name} [{stat_entry.tid_id}]"),
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


@mod.route("/stats/config", methods=["GET"])
@login_required
@aa_required
def get_config():
    return render_template("stats/config.html", stats_global=current_user.faction.stats_db_global)


@mod.route("/stats/config", methods=["POST"])
@login_required
@aa_required
def config():
    if (request.form.get("enabled") is not None) ^ (request.form.get("disabled") is not None):
        stats_global = request.form.get("enabled") is not None
        Faction.update(stats_db_global=stats_global).where(Faction.tid == current_user.faction_id).execute()

        return render_template("stats/config.html", stats_global=stats_global)

    # This should never occur as enabled/disabled are the only options in the form
    abort(400)


@mod.route("/stats/faction", methods=["POST"])
@login_required
def generate_faction_stats_csv():
    faction_id = request.form.get("faction-id")

    try:
        faction: Faction = Faction.select(Faction.name).where(Faction.tid == int(faction_id)).get()
    except (ValueError, DoesNotExist):
        return render_template(
            "errors/error.html", title="Invalid Faction ID", error="This faction ID could not be found in the database."
        )

    faction_members: typing.Tuple[typing.Tuple[int, str, int]]
    if current_user.key is None:
        faction_members = tuple(
            (user.tid, user.name, user.level)
            for user in User.select(User.tid, User.name, User.level).where(User.faction_id == faction_id)
        )
    else:
        faction_members_data = tornget(f"faction/{faction_id}?selections=basic", current_user.key)
        faction_members = tuple(
            (int(user_id), user_data["name"], user_data["level"])
            for user_id, user_data in faction_members_data["members"].items()
        )

    executor = ThreadPoolExecutor(max_workers=5)

    def _row(*values):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(values)
        return output.getvalue()

    def estimate_user_with_context(*args, **kwargs):
        with db.connection_context():
            return estimate_user(*args, **kwargs)

    @stream_with_context
    def generate_csv():
        yield _row("tid", "name", "level", "estimated_stat_score", "stat_score", "stat_score_timestamp")

        futures = {
            executor.submit(estimate_user_with_context, user[0], current_user.key, current_user.key is not None): user
            for user in faction_members
        }

        for future in as_completed(futures):
            user_id, user_name, user_level = futures[future]

            estimated_stat_score: typing.Optional[int]
            try:
                result = future.result()
                estimated_stat_score = int(result[0])
            except Exception:
                estimated_stat_score = None

            stat: typing.Optional[Stat]
            if current_user.faction_id not in (None, 0):
                stat = (
                    Stat.select()
                    .where(
                        (Stat.tid == user_id)
                        & ((Stat.added_group == 0) | (Stat.added_group == current_user.faction_id))
                    )
                    .order_by(Stat.time_added.desc())
                    .first()
                )
            else:
                stat = Stat.select().where((Stat.tid == user_id) & (Stat.added_group == 0)).first()

            yield _row(
                user_id,
                user_name,
                user_level,
                estimated_stat_score,
                None if stat is None else int(stat.battlescore),
                None if stat is None else int(stat.time_added.timestamp()),
            )

    return Response(
        generate_csv(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=faction-stats-{faction.name}-{datetime.datetime.utcnow().isoformat()}.csv"
        },
    )
