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
from mongoengine.queryset.visitor import Q
from tornium_commons.formatters import commas
from tornium_commons.models import FactionModel, UserModel

from models.faction import Faction


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

    if search_value == "":
        factions_db = FactionModel.objects()
    else:
        factions_db = FactionModel.objects(Q(name__startswith=search_value))

    if ordering_direction == "asc":
        ordering_direction = "+"
    else:
        ordering_direction = "-"

    if ordering == 0:
        factions_db = factions_db.order_by(f"{ordering_direction}tid")
    elif ordering == 1:
        factions_db = factions_db.order_by(f"{ordering_direction}name")
    else:
        factions_db = factions_db.order_by(f"{ordering_direction}respect")

    count = factions_db.count()
    factions_db = factions_db[start : start + length]

    faction: FactionModel
    for faction in factions_db:
        factions.append([faction.tid, faction.name, commas(faction.respect)])

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": FactionModel.objects().count(),
        "recordsFiltered": count,
        "data": factions,
    }

    return data


@login_required
def faction_data(tid: int):
    if tid == 0 or current_user.key == "":
        return abort(400)

    Faction(tid).refresh(key=current_user.key, force=True)
    faction: FactionModel = FactionModel.objects(tid=tid).first()

    leader: UserModel = UserModel.objects(tid=faction.leader).first()
    coleader: UserModel = UserModel.objects(tid=faction.coleader).first()

    return render_template(
        "torn/factionmodal.html",
        faction=faction,
        leader=leader,
        coleader=coleader,
    )


@login_required
def faction_members_data(tid: int):
    if tid == 0:
        abort(400)

    members = []

    member: UserModel
    for member in UserModel.objects(factionid=tid):
        members.append(
            {
                "username": f"{member.name} [{member.tid}]",
                "level": member.level,
                "last_action": member.last_action,
                "status": member.status,
                "discord_id": member.discord_id,
            }
        )

    return jsonify(members)
