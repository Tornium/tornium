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

import math

from flask import render_template
from flask_login import login_required
from mongoengine.queryset.visitor import Q

from tornium_commons.models import UserModel

from controllers.faction.decorators import fac_required


@login_required
@fac_required
def members(*args, **kwargs):
    fac_members = UserModel.objects(factionid=kwargs["faction"].tid)
    stats = []

    member: UserModel
    for member in fac_members:
        if member.battlescore == 0:
            continue

        stats.append(member.battlescore)

    stats.sort(reverse=True)
    stats = stats[: math.floor(0.8 * len(stats)) - 1]

    return render_template(
        "faction/members.html",
        members=fac_members,
        average_stat=UserModel.objects(Q(factionid=kwargs["faction"].tid) & Q(battlescore__ne=0)).average(
            "battlescore"
        ),
        average_stat_80=sum(stats) / len(stats) if len(stats) != 0 else 0,
    )
