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
import typing

from flask import render_template
from flask_login import current_user, login_required
from tornium_commons.models import Faction, User

from controllers.faction.decorators import fac_required


@login_required
@fac_required
def members(*args, **kwargs):
    fac_members: typing.Iterable[User] = (
        User.select(
            User.battlescore,
            User.key,
            User.tid,
            User.faction_aa,
            User.level,
            User.last_action,
            User.last_refresh,
            User.discord_id,
            User.name,
            User.strength,
            User.defense,
            User.speed,
            User.dexterity,
        )
        .join(Faction)
        .where(User.faction_id == int(current_user.faction.tid))
        .execute()
    )

    if current_user.faction_aa:
        stats = []

        member: User
        for member in fac_members:
            if member.battlescore in (None, 0):
                continue

            stats.append(member.battlescore)

        average = sum(stats) / len(stats) if len(stats) != 0 else 0

        stats.sort(reverse=True)
        stats = stats[: math.floor(0.8 * len(stats)) - 1]

        return render_template(
            "faction/members.html",
            members=fac_members,
            average_stat=average,
            average_stat_80=sum(stats) / len(stats) if len(stats) != 0 else 0,
        )
    else:
        return render_template(
            "faction/members.html",
            members=fac_members,
        )
