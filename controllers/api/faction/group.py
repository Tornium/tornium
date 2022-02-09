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
import uuid

from controllers.api.decorators import *
from models.factionmodel import FactionModel
from models.factiongroupmodel import FactionGroupModel
from models.user import User
import utils


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'faction:admin'})
def group_modify(*args, **kwargs):
    data = json.loads(request.get_data().decode('utf-8'))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user = User(kwargs['user'].tid)
    group: FactionGroupModel = utils.first(FactionGroupModel.objects(tid=data.get('groupid')))

    action = data.get('action')
    value = data.get('value')

    if group is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The provided faction group ID was not a valid ID.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif action is None or action not in ['name', 'remove', 'invite', 'delete', 'share-statdb']:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. There was no correct action provided but was required.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif value is None and action in ['name', 'share-statdb']:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. There was no correct value provided but was required.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif user.factiontid != group.creator and action not in ['share-statdb']:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The provided faction group can not be modified. Only AA '
                       'users within the creating faction can modify the faction group.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    if action == 'name':
        group.name = value
        group.save()
    elif action == 'remove':
        if value == group.creator:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The group creator can not be removed from the group.'
            }), 400, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }

        group.members.remove(value)
        group.save()
    elif action == 'invite':
        group.invite = uuid.uuid4().hex
        group.save()
    elif action == 'delete':
        for faction in group.members:
            faction: FactionModel = utils.first(FactionModel.objects(tid=faction))
            faction.groups.remove(group.tid)
            faction.save()

        group.delete()

        return jsonify({
            'code': 1,
            'name': 'OK',
            'message': 'Server request was successful.'
        }), 200, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif action == 'share-statdb':
        if value:
            group.sharestats.append(kwargs['user'].factionid)
        else:
            group.sharestats.remove(kwargs['user'].factionid)
        group.save()

    return jsonify({
        'tid': group.tid,
        'name': group.name,
        'creator': group.creator,
        'members': group.members,
        'sharestats': group.sharestats
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }
