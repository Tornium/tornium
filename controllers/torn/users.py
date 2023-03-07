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

from tornium_celery.tasks.user import update_user
from tornium_commons.formatters import commas, rel_time
from tornium_commons.models import FactionModel, PersonalStatModel, UserModel

from models.faction import Faction

USER_ORDERING = {
    0: "tid",
    1: "name",
    2: "level",
    3: "factionid",
    4: "last_action",
    5: "last_refresh",
}

PS_ORDERING = {
    0: "tid",
    2: "useractivity",
    3: "attackswon",
    4: "statenhancersused",
    5: "xantaken",
    6: "lsdtaken",
    7: "networth",
    8: "energydrinkused",
    9: "refills",
    10: "timestamp",
}


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

    if ordering in USER_ORDERING:
        users_db = users_db.order_by(f"{ordering_direction}{USER_ORDERING[ordering]}")
    else:
        users_db = users_db.order_by(f"{ordering_direction}last_refresh")

    count = users_db.count()
    users_db = users_db[start : start + length]

    user: UserModel
    for user in users_db:
        if user.factionid == 0:
            users.append(
                {
                    "tid": user.tid,
                    "name": user.name,
                    "level": user.level,
                    "faction": "None",
                    "last_action": {
                        "display": rel_time(user.last_action),
                        "timestamp": user.last_action,
                    },
                    "last_refresh": {
                        "display": rel_time(user.last_refresh),
                        "timestamp": user.last_refresh,
                    },
                }
            )
            continue

        faction: FactionModel = FactionModel.objects(tid=user.factionid).first()

        users.append(
            {
                "tid": user.tid,
                "name": user.name,
                "level": user.level,
                "faction": "Unknown" if faction is None else f"{faction.name} [{faction.tid}]",
                "last_action": {
                    "display": rel_time(user.last_action),
                    "timestamp": user.last_action,
                },
                "last_refresh": {
                    "display": rel_time(user.last_refresh),
                    "timestamp": user.last_refresh,
                },
            }
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": UserModel.objects().count(),
        "recordsFiltered": count,
        "data": users,
    }

    return data


@login_required
def users_ps_data():
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))
    search_value = request.args.get("search[value]")
    ordering = int(request.args.get("order[0][column]"))
    ordering_direction = request.args.get("order[0][dir]")

    users = []

    if search_value == "":
        ps_db = PersonalStatModel.objects()
    else:
        valid_tid = [user.tid for user in UserModel.objects(Q(name__startswith=search_value)).only("tid").all()]
        ps_db = PersonalStatModel.objects(tid__in=valid_tid)

    if ordering_direction == "asc":
        ordering_direction = "+"
    else:
        ordering_direction = "-"

    if ordering in PS_ORDERING:
        print(PS_ORDERING[ordering])
        ps_db = ps_db.order_by(f"{ordering_direction}{PS_ORDERING[ordering]}")
    else:
        ps_db = ps_db.order_by(f"{ordering_direction}timestamp")

    count = ps_db.count()
    ps_db = ps_db[start : start + length]

    ps: PersonalStatModel
    for ps in ps_db:
        user: UserModel = UserModel.objects(tid=ps.tid).only("name").first()
        user_data = {
            "tid": ps.tid,
            "name": "N/A",
            "useractivity": {
                "display": ps.useractivity,
                "sort": ps.useractivity,
            },
            "attackswon": ps.attackswon,
            "statenhancersused": ps.statenhancersused,
            "xanused": ps.xantaken,
            "lsdused": ps.lsdtaken,
            "networth": f"${commas(ps.networth)}",
            "energydrinkused": ps.energydrinkused,
            "refills": ps.refills,
            "update": {
                "display": rel_time(ps.timestamp),
                "timestamp": ps.timestamp,
            },
        }

        if user is not None:
            user_data["name"] = user.name

        users.append(user_data)

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": PersonalStatModel.objects().count(),
        "recordsFiltered": count,
        "data": users,
    }

    return data


@login_required
def user_data(tid: int):
    if tid == 0:
        abort(400)

    update_user(current_user.key, tid=tid, wait=True)
    user: UserModel = UserModel.objects(tid=tid).first()
    Faction(user.factionid).refresh(key=current_user.key)
    faction: FactionModel = FactionModel.objects(tid=user.factionid).first()

    return render_template("torn/usermodal.html", user=user, faction=faction)
