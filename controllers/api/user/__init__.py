# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

from controllers.api.decorators import *


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'read:user'})
def get_user(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    return jsonify({
        'tid': kwargs['user'].tid,
        'name': kwargs['user'].name,
        'username': f'{kwargs["user"].name} [{kwargs["user"].tid}]',
        'last_refresh': kwargs['user'].last_refresh,
        'battlescore': kwargs['user'].battlescore,
        'battlescore_update': kwargs['user'].battlescore_update,
        'discord_id': kwargs['user'].discord_id,
        'servers': kwargs['user'].servers,
        'factiontid': kwargs['user'].factionid,
        'aa': kwargs['user'].factionaa,
        'status': kwargs['user'].status,
        'last_action': kwargs['user'].last_action,
        'pro': kwargs['user'].pro,
        'pro_expiration': kwargs['user'].pro_expiration
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }
