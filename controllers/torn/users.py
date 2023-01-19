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

from flask import abort, render_template, request
from flask_login import current_user, login_required
from mongoengine.queryset.visitor import Q

from models.faction import Faction
from models.factionmodel import FactionModel
from models.user import User
from models.usermodel import UserModel


@login_required
def users():
    return render_template("torn/users.html")


@login_required
def users_data():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    search_value = request.args.get("search[value]")
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")

    users = []

    if search_value == "":
        users_db = UserModel.objects()
    else:
        users_db = UserModel.objects(Q(name__startswith=search_value))

    if ordering_direction == "asc":
        ordering_direction = "+"
    else:
        ordering_direction = "-"

    if ordering == 0:
        users_db = users_db.order_by(f"{ordering_direction}tid")
    elif ordering == 1:
        users_db = users_db.order_by(f"{ordering_direction}name")
    else:
        users_db = users_db.order_by(f"{ordering_direction}level")

    count = users_db.count()
    users_db = users_db[start : start + length]

    user: UserModel
    for user in users_db:
        users.append([user.tid, user.name, user.level])

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": UserModel.objects().count(),
        "recordsFiltered": count,
        "data": users,
    }

    return data


@login_required
def user_data(tid: int):
    if tid == 0:
        abort(400)

    User(tid).refresh(key=current_user.key, force=True)
    user: UserModel = UserModel.objects(tid=tid).first()
    Faction(user.factionid).refresh(key=current_user.key)
    faction: FactionModel = FactionModel.objects(tid=user.factionid).first()

    return render_template("torn/usermodal.html", user=user, faction=faction)
