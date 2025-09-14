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

import datetime

from tornium_commons.models import Retaliation, User

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth("faction:attacks", "faction")
@ratelimit
def get_faction_retaliations(faction_id: int, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user: User = kwargs["user"]

    if user.faction_id != faction_id:
        return make_exception_response("4022", key)

    Attacker = User.alias()
    retals = (
        Retaliation.select()
        .join(User, on=Retaliation.defender)
        .switch(Retaliation)
        .join(Attacker, on=Retaliation.attacker)
        .where(
            (User.faction_id == faction_id)
            & (Retaliation.attack_ended >= datetime.datetime.utcnow() - datetime.timedelta(minutes=5))
        )
        .order_by(Retaliation.attack_ended.desc())
        .limit(250)
    )

    return [retal.to_dict() for retal in retals], 200, api_ratelimit_response(key)
