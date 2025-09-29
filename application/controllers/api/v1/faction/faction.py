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

from tornium_commons.models import Faction, User

from controllers.api.v1.decorators import ratelimit, require_oauth
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth()
@ratelimit
def faction_members(faction_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    return (
        [member.to_dict() for member in User.select().where(User.faction_id == faction_id)],
        200,
        api_ratelimit_response(key),
    )
