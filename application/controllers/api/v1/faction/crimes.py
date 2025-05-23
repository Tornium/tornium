# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import typing

from flask import jsonify
from tornium_commons.models import Faction, OrganizedCrimeCPR, OrganizedCrimeNew, User

from controllers.api.v1.decorators import (
    global_cache,
    ratelimit,
    require_oauth,
    session_required,
)
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth()
@ratelimit
@global_cache
def get_oc_names(*args, **kwargs):
    return jsonify(OrganizedCrimeNew.oc_names()), 200, api_ratelimit_response(f"tornium:ratelimit:{kwargs['user'].tid}")


@session_required
@ratelimit
def get_members_cpr(faction_id: int, oc_name: str, oc_position_name: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if oc_name not in OrganizedCrimeNew.oc_names():
        return make_exception_response("1105", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4004", key)
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    members = [member.tid for member in User.select(User.tid).where(User.faction_id == faction_id)]
    members_cpr: typing.Iterable[OrganizedCrimeCPR] = (
        OrganizedCrimeCPR.select()
        .join(User)
        .where(
            (User.tid.in_(members))
            & (OrganizedCrimeCPR.oc_name == oc_name)
            & (OrganizedCrimeCPR.oc_position == oc_position_name)
        )
    )

    return (
        {
            member.user_id: {"cpr": member.cpr, "name": member.user.name, "updated_at": member.updated_at}
            for member in members_cpr
        },
        200,
        api_ratelimit_response(key),
    )
