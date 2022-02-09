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

import os
import uuid

from flask import send_file

from controllers.api.decorators import *
from models.schedule import Schedule
from models.schedulemodel import ScheduleModel
from models.user import User


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def create_schedule(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
           'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
           'X-RateLimit-Remaining': client.get(key),
           'X-RateLimit-Reset': client.ttl(key)
        }

    schedule = Schedule(uuid=uuid.uuid4().hex, factiontid=user.factiontid)

    return schedule.file, 200, {
       'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
       'X-RateLimit-Remaining': client.get(key),
       'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def delete_schedule(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    data = json.loads(request.get_data().decode('utf-8'))
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    Schedule(uuid=data['uuid'], factiontid=user.factiontid).delete()

    return {
        'code': 0,
        'name': 'OK',
        'message': 'Server request was successful.'
    }, 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def add_chain_watcher(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    data = json.loads(request.get_data().decode('utf-8'))
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    schedule = Schedule(uuid=data['uuid'], factiontid=user.factiontid)
    schedule.add_activity(tid=data['tid'], activity=None)
    schedule.set_weight(tid=data['tid'], weight=data['weight'])

    return schedule.file, 200, {
       'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
       'X-RateLimit-Remaining': client.get(key),
       'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def remove_chain_watcher(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    data = json.loads(request.get_data().decode('utf-8'))
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    schedule = Schedule(uuid=data['uuid'], factiontid=user.factiontid)
    schedule.remove_user(data['tid'])

    return schedule.file, 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def add_chain_availability(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    data = json.loads(request.get_data().decode('utf-8'))
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    if data.get('from') is None or data.get('to') is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Sever failed to fulfill the request. The from and to values are required for this endpoint.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif data.get('to') <= data.get('from'):
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Sever failed to fulfill the request. The to value must be greater than the from value.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    schedule = Schedule(uuid=data['uuid'], factiontid=user.factiontid)

    if int(data['from']) < schedule.fromts or int(data['to']) > schedule.tots:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Sever failed to fulfill the request. The interval must be within the specified chain '
                       'interval or the chain interval must be set.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    for activity in schedule.activity[data['tid']]:
        fromts = int(activity.split('-')[0])
        tots = int(activity.split('-')[1])

        if data['from'] <= tots and data['to'] >= fromts:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Sever failed to fulfill the request. The interval must be within the specified chain '
                           'interval or the chain interval must be set.'
            }), 400, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }

    schedule.add_activity(tid=data['tid'], activity=f'{data["from"]}-{data["to"]}')

    return schedule.file, 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def schedule_setup(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    data = json.loads(request.get_data().decode('utf-8'))
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    if data.get('from') is None or data.get('to') is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Sever failed to fulfill the request. The from and to values are required for this endpoint.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif data.get('to') <= data.get('from'):
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Sever failed to fulfill the request. The to value must be greater than the from value.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    schedule = Schedule(uuid=data['uuid'], factiontid=user.factiontid)
    schedule.fromts = int(data.get('from'))
    schedule.tots = int(data.get('to'))
    schedule.update_file()

    return schedule.file, 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'execute:faction', 'faction:admin'})
def execute_scheduler(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    try:
        schedule = Schedule(uuid=uuid, factiontid=user.factiontid)
    except Exception:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'due to a cross-faction request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    if schedule.factiontid != user.factiontid:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'due to a cross-faction request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    schedule.generate()
    return schedule.schedule, 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'read:faction', 'faction:admin'})
def get_schedule(uuid, *args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    if uuid is not None:
        try:
            schedule = Schedule(uuid=uuid, factiontid=user.factiontid)
        except Exception:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                           'due to a cross-faction request.'
            }), 403, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }

        if schedule.factiontid != user.factiontid:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                           'due to a cross-faction request.'
            }), 403, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }

        return send_file(f'{os.getcwd()}/schedule/{uuid}.json'), 200, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    else:
        schedules = []
        for schedule in ScheduleModel.objects(factiontid=user.factiontid):
            schedules.append(schedule.uuid)

        return jsonify(schedules), 200, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
