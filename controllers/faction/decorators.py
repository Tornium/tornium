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

from functools import wraps

from flask import abort
from flask_login import current_user

from tornium_commons.models import FactionModel


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
