# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json

from controllers.api.decorators import *
from models.astatmodel import AStatModel
import utils


@key_required
@ratelimit
@pro_required
@requires_scopes(scopes={'admin', 'write:stats', 'admin:stats'})
def attack_start(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    network_attack = json.loads(request.get_data().decode('utf-8'))

    if network_attack['DB']['attackStatus'] != 'notStarted':
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. An illegal attack status was passed.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif kwargs['user'].strength == 0 or kwargs['user'].defense == 0 or kwargs['user'].speed == 0 or kwargs['user'].dexterity == 0:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user has no battlestats stored.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    attack = AStatModel(
        sid=AStatModel.objects().count(),
        logid=network_attack['DB']['logID'],
        tid=network_attack['DB']['attackerUser']['userID'],
        timeadded=utils.now(),
        addedid=kwargs['user'].tid,
        attackstr=kwargs['user'].strength,
        attackerdef=kwargs['user'].defense,
        attackerspd=kwargs['user'].speed,
        attackerdex=kwargs['user'].dex
    )
    attack.save()

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
@requires_scopes(scopes={'admin', 'write:stats', 'admin:stats'})
def attack_hit(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    network_attack = json.loads(request.get_data().decode('urf-8'))

    if network_attack['DB']['attackStatus'] != 'start':
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. An illegal attack status was passed.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif kwargs['user'].strength == 0 or kwargs['user'].defense == 0 or kwargs['user'].speed == 0 or kwargs['user'].dexterity == 0:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user has no battlestats stored.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    attack: AStatModel = AStatModel.objects(logid=network_attack['DB']['logID'])[-1]
    attack.status = network_attack['DB']['attackStatus']
    attack.attackerhits.append(network_attack['DB']['attacker'])
    attack.defenderhits.append(network_attack['DB']['defender'])
    attack.save()

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
@requires_scopes(scopes={'admin', 'write:stats', 'admin:stats'})
def attack_end(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    network_attack = json.loads(request.get_data().decode('urf-8'))

    if network_attack['DB']['attackStatus'] != 'end':
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. An illegal attack status was passed.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    elif kwargs['user'].strength == 0 or kwargs['user'].defense == 0 or kwargs['user'].speed == 0 or kwargs['user'].dexterity == 0:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user has no battlestats stored.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    attack: AStatModel = AStatModel.objects(logid=network_attack['DB']['logID'])[-1]
    attack.status = network_attack['DB']['attackStatus']
    attack.attackerhits.append(network_attack['DB']['attacker'])
    attack.defenderhits.append(network_attack['DB']['defender'])
    attack.save()

    return jsonify({
        'code': 1,
        'name': 'OK',
        'message': 'Server request was successful.'
    }), 200, {
        'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
        'X-RateLimit-Remaining': client.get(key),
        'X-RateLimit-Reset': client.ttl(key)
    }
