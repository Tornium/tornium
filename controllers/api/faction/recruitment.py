# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json
import uuid

from mongoengine.queryset.visitor import Q

from controllers.api.decorators import *
from models.recruitmodel import RecruitModel
import redisdb
from tasks import tornget


@key_required
@ratelimit
@pro_required
@requires_scopes(scopes={'admin', 'faction:admin'})
def add_recruiter(*args, **kwargs):
    data = json.loads(request.get_data().decode('utf-8'))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    user = data.get('user')

    if user is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. There was no user provided but was required.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    try:
        user = int(user)
    except ValueError:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. Illegal user ID provided.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    user: UserModel = utils.first(UserModel.objects(tid=user))

    if user is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. Illegal user ID provided.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif user.factionid != kwargs['user'].factionid:
        return jsonify({
            'code': 0,
            'name': 'PermissionDenied',
            'message': 'Server failed to fulfill the request. The user is not in your faction or is not signed in.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif not kwargs['user'].factionaa:
        return jsonify({
            'code': 0,
            'name': 'PermissionDenied',
            'message': 'Server failed to fulfill the request. The current user is not an AA member of their current '
                       'faction.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif user.recruiter:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user is already a recruiter.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    user.recruiter = True
    user.save()

    return jsonify({
        'code': 1,
        'name': 'OK',
        'message': 'Server request was successful.'
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@pro_required
@requires_scopes(scopes={'admin', 'faction:admin'})
def remove_recruiter(*args, **kwargs):
    data = json.loads(request.get_data().decode('utf-8'))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    user = data.get('user')

    if user is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. There was no user provided but was required.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    try:
        user = int(user)
    except ValueError:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. Illegal user ID provided.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    user: UserModel = utils.first(UserModel.objects(tid=user))

    if user is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. Illegal user ID provided.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif user.factionid != kwargs['user'].factionid:
        return jsonify({
            'code': 0,
            'name': 'PermissionDenied',
            'message': 'Server failed to fulfill the request. The user is not in your faction or is not signed in.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif not kwargs['user'].factionaa:
        return jsonify({
            'code': 0,
            'name': 'PermissionDenied',
            'message': 'Server failed to fulfill the request. The current user is not an AA member of their current '
                       'faction.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif not user.recruiter:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user is not yet a recruiter.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    user.recruiter = False
    user.save()

    return jsonify({
        'code': 1,
        'name': 'OK',
        'message': 'Server request was successful.'
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@pro_required
@requires_scopes(scopes={'admin', 'faction:admin'})
def refresh_code(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    if not kwargs['user'].recruiter:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user is not currently a recruiter.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    code = uuid.uuid4().hex[:8]

    if utils.first(UserModel.objects(recruiter_code=code)) is not None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The generated recruiter code was already found. '
                       'Please try again.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    user: UserModel = utils.first(UserModel.objects(tid=kwargs['user'].tid))

    if user is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The current user could not be found in the database.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    user.recruiter_code = code
    user.save()

    return jsonify({
        'user': user.tid,
        'recruiter_code': user.recruiter_code
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }


@key_required
@ratelimit
@pro_required
@requires_scopes(scopes={'admin', 'faction:admin'})
def message_send(*args, **kwargs):
    data = json.loads(request.get_data().decode('utf-8'))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    if not kwargs['user'].recruiter:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user is not currently a recruiter.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif not kwargs['user'].factionaa:
        return jsonify({
            'code': 0,
            'name': 'PermissionDenied',
            'message': 'Server failed to fulfill the request. The current user is not an AA member of their current '
                       'faction.'
        }), 403, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    if data.get('receiver') is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. No receiver was specified in the request.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    try:
        receiver_data = tornget(f'user/{utils.get_tid(data.get("receiver"))}?selections=', key=kwargs['user'].key)
    except utils.TornError as e:
        if e.code == 6:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. An illegal receiver was specified in the request.'
            }), 400, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }
        else:
            return jsonify({
                'code': 4100,
                'name': 'TornError',
                'message': 'Server failed to fulfill the request. The Torn API has returned an error.',
                'error': {
                    'code': e.code,
                    'error': e.error,
                    'message': e.message
                }
            }), 400, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }
    except utils.NetworkingError as e:
        return jsonify({
            'code': 4101,
            'name': 'NetworkingError',
            'message': 'Server failed to fulfill the request. The Torn or Discord API has returned a networking error.',
            'error': {
                'code': e.code,
                'message': e.message
            }
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    recruit: RecruitModel = utils.first(RecruitModel.objects(Q(tid=receiver_data['player_id']) & Q(factionid=kwargs['user'].factionid) & Q(recruiter=kwargs['user'].tid)))

    if recruit is None:
        recruit = RecruitModel(
            uuid=uuid.uuid4().hex,
            tid=receiver_data['player_id'],
            factionid=kwargs['user'].factionid,
            recruiter=kwargs['user'].tid,
            messages_received=1,
            tif=0,
            status=0
        )
    else:
        recruit.messages_received += 1

    recruit.save()

    return jsonify({
        'uuid': recruit.uuid,
        'tid': recruit.tid,
        'factionid': recruit.factionid,
        'recruiter': recruit.recruiter,
        'messages_received': recruit.messages_received,
        'tif': recruit.tif,
        'status': recruit.status
    })
