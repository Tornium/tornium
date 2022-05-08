# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import uuid

from flask import render_template, redirect
from flask_login import login_required

from controllers.faction.decorators import *
from models.factiongroupmodel import FactionGroupModel
from models.factionmodel import FactionModel
import utils


@login_required
@fac_required
@aa_required
def groups(*args, **kwargs):
    return render_template(
        "faction/groups.html",
        groups=[
            utils.first(FactionGroupModel.objects(tid=group))
            for group in utils.first(
                FactionModel.objects(tid=current_user.factiontid)
            ).groups
        ],
    )


@login_required
@fac_required
@aa_required
def create_group(*args, **kwargs):
    faction: FactionModel = utils.first(
        FactionModel.objects(tid=current_user.factiontid)
    )

    if faction is None:
        return render_template(
            "errors/error.html",
            title="Faction Missing",
            error="No faction was found to be " "attached to the logged in user.",
        )

    group = FactionGroupModel(
        tid=utils.last(FactionGroupModel.objects()).tid + 1,
        name=str(utils.last(FactionGroupModel.objects()).tid + 1),
        creator=current_user.factiontid,
        members=[faction.tid],
        invite=uuid.uuid4().hex,
    )
    group.save()

    faction.groups.append(group.tid)
    faction.save()

    return redirect(f"/faction/group/{group.tid}")


@login_required
@fac_required
@aa_required
def group_invite(invite: str, *args, **kwargs):
    dbgroup: FactionGroupModel = utils.first(FactionGroupModel.objects(invite=invite))
    faction: FactionModel = utils.first(
        FactionModel.objects(tid=current_user.factiontid)
    )

    if faction is None:
        return render_template(
            "errors/error.html",
            title="Faction Missing",
            error="No faction was found to be " "attached to the logged in user.",
        )
    elif dbgroup is None:
        return render_template(
            "errors/error.html",
            title="Faction Group Missing",
            error="No faction group was found " "with the specific ID.",
        )
    elif dbgroup.tid in faction.groups:
        return render_template(
            "errors/error.html",
            title="Error",
            error="Faction is already a member of the group.",
        )

    dbgroup.members.append(current_user.factiontid)
    dbgroup.save()

    faction.groups.append(dbgroup.tid)
    faction.save()

    return redirect(f"/faction/group/{dbgroup.tid}")


@login_required
@fac_required
@aa_required
def group(tid: int, *args, **kwargs):
    dbgroup: FactionGroupModel = utils.first(FactionGroupModel.objects(tid=tid))
    faction: FactionModel = utils.first(
        FactionModel.objects(tid=current_user.factiontid)
    )

    if faction is None:
        return render_template(
            "errors/error.html",
            title="Faction Missing",
            error="No faction was found to be " "attached to the logged in user.",
        )
    elif dbgroup is None:
        return render_template(
            "errors/error.html",
            title="Faction Group Missing",
            error="No faction group was found " "with the specific ID.",
        )

    return render_template(
        "faction/group.html",
        group=dbgroup,
        members=[
            utils.first(FactionModel.objects(tid=int(member)))
            for member in dbgroup.members
        ],
        key=current_user.key,
        faction=faction,
    )
