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
from peewee import DoesNotExist
from tornium_celery.tasks.user import update_user
from tornium_commons.formatters import commas, rel_time
from tornium_commons.models import Faction, PersonalStats, User


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
    users_db = User.select()

    if search_value != "":
        users_db = users_db.where(User.name.startswith(search_value))

    if ordering_direction == "asc":
        ordering_direction = 1
    else:
        ordering_direction = -1

    if ordering == 0:
        users_db = users_db.order_by(ordering_direction * User.tid)
    elif ordering == 1:
        users_db = users_db.order_by(ordering_direction * User.name)
    elif ordering == 2:
        users_db = users_db.order_by(ordering_direction * User.level)
    elif ordering == 3:
        users_db = users_db.order_by(ordering_direction * User.faction_id)
    elif ordering == 4:
        users_db = users_db.order_by(ordering_direction * User.last_action)
    else:
        users_db = users_db.order_by(ordering_direction * User.last_refresh)

    count = users_db.count()
    users_db = users_db[start : start + length]

    user: User
    for user in users_db:
        users.append(
            {
                "tid": user.tid,
                "name": user.name,
                "level": user.level,
                "faction": ("Unknown" if user.faction is None else f"{user.faction.name} [{user.faction_id}]"),
                "last_action": {
                    "display": (rel_time(user.last_action) if user.last_action is not None else ""),
                    "timestamp": user.last_action,
                },
                "last_refresh": {
                    "display": (rel_time(user.last_refresh) if user.last_refresh is not None else ""),
                    "timestamp": user.last_refresh,
                },
            }
        )

    data = {
        "draw": request.args.get("draw"),
        "recordsTotal": User.select().count(),
        "recordsFiltered": count,
        "data": users,
    }

    return data


@login_required
def user_data(tid: int):
    if tid == 0 or current_user.key is None:
        return abort(400)

    update_user(current_user.key, tid=tid)

    try:
        user: User = User.get_by_id(tid)
    except DoesNotExist:
        return abort(400)

    return render_template("torn/usermodal.html", user=user)
