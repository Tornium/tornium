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

from flask import jsonify

from controllers.api.decorators import authentication_required, ratelimit
from controllers.api.utils import api_ratelimit_response


@authentication_required
@ratelimit
def get_user(*args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    return (
        jsonify(
            {
                "tid": kwargs["user"].tid,
                "name": kwargs["user"].name,
                "username": f'{kwargs["user"].name} [{kwargs["user"].tid}]',
                "last_refresh": kwargs["user"].last_refresh,
                "battlescore": kwargs["user"].battlescore,
                "battlescore_update": kwargs["user"].battlescore_update,
                "discord_id": kwargs["user"].discord_id,
                "factiontid": kwargs["user"].factionid,
                "aa": kwargs["user"].factionaa,
                "status": kwargs["user"].status,
                "last_action": kwargs["user"].last_action,
            }
        ),
        200,
        api_ratelimit_response(key),
    )
