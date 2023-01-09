# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from functools import wraps

from flask import abort
from flask_login import current_user

import utils
from models.factionmodel import FactionModel


def aa_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.aa:
            return abort(403)
        else:
            return f(*args, **kwargs)

    return wrapper


def fac_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.factiontid == 0:
            return abort(403, "User is not in a faction.")

        faction = FactionModel.objects(tid=current_user.factiontid).first()

        if faction is None:
            return abort(403, "User is not in a faction stored in the database.")

        kwargs["faction"] = faction
        return f(*args, **kwargs)

    return wrapper
