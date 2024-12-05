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
from tornium_commons.formatters import commas
from tornium_commons.models import Faction, User


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

