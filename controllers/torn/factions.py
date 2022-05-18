#  Copyright (C) tiksan - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by tiksan <webmaster@deek.sh>

from flask import render_template, request, abort
from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q

from models.faction import Faction
from models.factionmodel import FactionModel
from models.statmodel import StatModel
from models.user import User
from models.usermodel import UserModel
import utils


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
        factions.append([faction.tid, faction.name, utils.commas(faction.respect)])

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": FactionModel.objects().count(),
        "recordsFiltered": count,
        "data": factions,
    }

    return data


@login_required
def faction_data(tid: int):
    if tid == 0:
        abort(400)

    Faction(tid).refresh(key=current_user.key, force=True)
    faction: FactionModel = utils.first(FactionModel.objects(tid=tid))

    members = []

    member: UserModel
    for member in UserModel.objects(factionid=tid):
        members.append(member)

    leader = User(faction.leader).refresh(key=current_user.key)
    if faction.coleader != 0 :
        coleader = User(faction.coleader).refresh(key=current_user.key)

    leader: UserModel = utils.first(UserModel.objects(tid=faction.leader))
    coleader: UserModel = utils.first(UserModel.objects(tid=faction.coleader))

    return render_template("torn/factionmodal.html", faction=faction, members=members, leader=leader, coleader=coleader)
