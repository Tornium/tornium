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

from flask import abort, jsonify, render_template, request
from flask_login import current_user, login_required
from peewee import DoesNotExist
from tornium_celery.tasks.api import tornget
from tornium_celery.tasks.faction import update_faction
from tornium_commons import rds
from tornium_commons.formatters import commas
from tornium_commons.models import Faction, MemberReport, User


@login_required
def factions():
    return render_template("torn/factions.html")


@login_required
def factions_data():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    search_value = request.args.get("search[value]")
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")

    factions = []
    factions_db = Faction.select(Faction.tid, Faction.name, Faction.respect)

    if search_value != "":
        factions_db = factions_db.where(Faction.name.startswith(search_value))

    if ordering_direction == "asc":
        ordering_direction = 1
    else:
        ordering_direction = -1

    if ordering == 0:
        factions_db = factions_db.order_by(ordering_direction * Faction.tid)
    elif ordering == 1:
        factions_db = factions_db.order_by(ordering_direction * Faction.name)
    else:
        factions_db = factions_db.order_by(ordering_direction * Faction.respect)

    count = factions_db.count()
    factions_db = factions_db[start : start + length]

    faction: Faction
    for faction in factions_db:
        factions.append(
            [
                faction.tid,
                faction.name,
                0 if faction.respect is None else commas(faction.respect),
            ]
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": Faction.select().count(),
        "recordsFiltered": count,
        "data": factions,
    }

    return data


@login_required
def faction_data(tid: int):
    if tid == 0 or current_user.key is None:
        return abort(400)

    tornget.signature(
        kwargs={"endpoint": f"faction/{tid}?selections=", "key": current_user.key},
        queue="api",
    ).apply_async(expires=300, link=update_faction.s())

    try:
        faction: Faction = (
            Faction.select(Faction.name, Faction.tid, Faction.coleader, Faction.leader).where(Faction.tid == tid).get()
        )
    except DoesNotExist:
        return render_template(
            "errors/error.html",
            title="Unknown Faction",
            error=f"Faction with ID {tid} could not be located in the database.",
        )

    return render_template("torn/factionmodal.html", faction=faction)


@login_required
def faction_members_data(tid: int):
    if tid == 0:
        abort(400)

    members = []

    member: User
    for member in (
        User.select(
            User.name,
            User.tid,
            User.level,
            User.last_action,
            User.status,
            User.discord_id,
        )
        .join(Faction)
        .where(User.faction_id == tid)
    ):
        members.append(
            {
                "username": f"{member.name} [{member.tid}]",
                "level": member.level,
                "last_action": (member.last_action.timestamp() if member.last_action is not None else None),
                "status": member.status,
                "discord_id": member.discord_id,
            }
        )

    return jsonify(members)


@login_required
def faction_members_report():
    if current_user.faction_id not in [15644, 12894]:
        return (
            "Permission Denied... This page is currently being tested by NSO factions. Please check back later.",
            403,
        )

    ps_keys = tuple(rds().smembers("tornium:personal-stats"))

    if len(ps_keys) == 0:
        ps_data = tornget("user/?selections=personalstats", key=current_user.key)

        if "code" in ps_data:
            return (
                render_template(
                    "errors/error.html",
                    title="Invalid API Data",
                    error="The Torn API returned invalid data that prevented this page from loading.",
                ),
                500,
            )

        ps_keys = tuple(ps_data["personalstats"].keys())
        n = rds().sadd("tornium:personal-stats", *ps_keys)

        if n > 0:
            rds().expire("tornium:personal-stats", 3600, nx=True)

    return render_template("torn/memberreport.html", ps_keys=ps_keys)


@login_required
def view_member_report(rid: str):
    if current_user.faction_id not in [15644, 12894]:
        return (
            "Permission Denied... This page is currently being tested by NSO factions. Please check back later.",
            403,
        )

    try:
        report: MemberReport = MemberReport.get_by_id(rid)
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Report",
                error="No report could be located with the included ID.",
            ),
            400,
        )

    if (report.requested_by_user is not None and report.requested_by_user != current_user.tid) or (
        report.requested_by_faction is not None and report.requested_by_faction != current_user.faction_id
    ):
        return render_template(
            "errors/error.html",
            title="Permission Denied",
            error="You do not have access to this report.",
        )

    return render_template("torn/memberreportview.html", report=report)
