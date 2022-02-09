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

import json
import secrets

from controllers.api.decorators import *
from models.keymodel import KeyModel
from models.user import User
import utils


@key_required
@ratelimit
def test_key(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    return jsonify({
        'code': 1,
        'name': 'OK',
        'message': 'Server request was successful. Authentication was successful.'
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@torn_key_required
@ratelimit
def create_key(*args, **kwargs):
    # curl -X POST -H "Authorization: Basic " -H "Content-Type: application/json" -d '{"scopes": []}' localhost:8000/api/key
    user = User(kwargs['user'].tid)
    data = json.loads(request.get_data().decode('utf-8'))

    scopes = data.get('scopes')
    expires = data.get('expires')

    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    if expires is not None and expires <= utils.now():
        return jsonify({
            'code': 0,
            'name': 'InvalidExpiryTimestamp',
            'message': 'Server failed to create the key. The provided timestamp was greater than the current '
                       'timestamp on the server.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    if scopes is None:
        scopes = []

    for scope in scopes:
        if scope not in []:
            return jsonify({
                'code': 0,
                'name': 'InvalidScope',
                'message': 'Server failed to create the key. The provided array of scopes included an invalid scope.'
            }), 400, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }

    key = base64.b64encode(f'{user.tid}:{secrets.token_urlsafe(32)}'.encode('utf-8')).decode('utf-8')
    keydb = KeyModel(
        key=key,
        ownertid=user.tid,
        scopes=scopes
    )
    keydb.save()

    return jsonify({
        'key': key,
        'ownertid': user.tid,
        'scopes': scopes,
        'expires': expires
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@torn_key_required
@ratelimit
def remove_key(*args, **kwargs):
    data = json.loads(request.get_data().decode('utf-8'))
    key = data.get('key')
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    
    if key is None:
        return

    key = utils.first(KeyModel.objects(key=key))
    owner = key.tid
    scopes = key.scopes
    expires = key.expires
    key.delete()
    key.save()
    
    return jsonify({
        'key': key,
        'ownerid': owner,
        'scopes': json.loads(scopes),
        'expires': expires
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }
