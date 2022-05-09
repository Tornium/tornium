#  Copyright (C) tiksan - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by tiksan <webmaster@deek.sh>

from flask import render_template, request
from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q

from models.faction import Faction
from models.factionmodel import FactionModel
from models.user import User
from models.usermodel import UserModel
import utils


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
    User(tid).refresh(key=current_user.key, force=True)
    user: UserModel = utils.first(UserModel.objects(tid=tid))
    Faction(tid).refresh(key=current_user.key)
    faction: FactionModel = utils.first(FactionModel.objects(tid=user.factionid))

    return render_template("torn/usermodal.html", user=user, faction=faction)
