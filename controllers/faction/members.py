#  Copyright (C) tiksan - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by tiksan <webmaster@deek.sh>

import math

from flask import render_template, request
from flask_login import login_required
from mongoengine.queryset.visitor import Q

from controllers.faction.decorators import *
from models.usermodel import UserModel


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
        average_stat=UserModel.objects(
            Q(factionid=kwargs["faction"].tid) & Q(battlescore__ne=0)
        ).average("battlescore"),
        average_stat_80=sum(stats) / len(stats) if len(stats) != 0 else 0,
    )
