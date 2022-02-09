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

from controllers.api.decorators import *
from models.faction import Faction
from models.server import Server
from models.user import User
from models.withdrawalmodel import WithdrawalModel
import tasks
import utils


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:banking', 'write:faction', 'faction:admin'})
def banking_request(*args, **kwargs):
    data = json.loads(request.get_data().decode('utf-8'))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    user = User(kwargs['user'].tid)
    amount_requested = data.get('amount_requested')

    if amount_requested is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. There was no amount requested provided but an amount '
                       'requested was required.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    
    amount_requested = str(amount_requested)

    if amount_requested.lower() != 'all':
        amount_requested = int(amount_requested)
    else:
        amount_requested = 'all'

    user.refresh()

    if user.factiontid == 0:
        user.refresh(force=True)

        if user.factiontid == 0:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The API key\'s user is required to be in a Torn '
                           'faction.'
            }), 400, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }

    faction = Faction(user.factiontid, key=user.key)
    
    if faction.guild == 0:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The faction does not currently have a Discord server set.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    
    server = Server(faction.guild)

    if faction.tid not in server.factions:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user\'s faction is not in the stored server\'s list '
                       'of factions.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    vault_config = faction.vault_config
    config = faction.config

    if vault_config.get('banking') == 0 or vault_config.get('banker') == 0 or config.get('vault') == 0:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user\'s faction\'s bot configuration needs to be '
                       'configured by faction AA members.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }

    vault_balances = tasks.tornget(f'faction/?selections=donations', faction.rand_key())

    if str(user.tid) in vault_balances['donations']:
        if amount_requested != 'all' and amount_requested > vault_balances['donations'][str(user.tid)]['money_balance']:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The amount requested was greater than the amount in '
                           'the user\'s faction vault balance.'
            }), 400, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }
        elif amount_requested == 'all' and vault_balances['donations'][str(user.tid)]['money_balance'] <= 0:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The user has no cash in the faction vault or a '
                           'negative vault balance.'
            }), 400, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(key),
                'X-RateLimit-Reset': client.ttl(key)
            }

        request_id = WithdrawalModel.objects().count()

        if amount_requested != 'all':
            message_payload = {
                'content': f'<@&{vault_config["banker"]}>',
                'embeds': [
                    {
                        'title': f'Vault Request #{request_id}',
                        'description': f'{user.name} [{user.tid}] is requesting {amount_requested} from the '
                                       f'faction vault. '
                                       f'To fulfill this request, enter `?f {request_id}` in this channel.',
                        'timestamp': datetime.datetime.utcnow().isoformat()
                    }
                ]
            }
        else:
            message_payload = {
                'content': f'<@&{vault_config["banker"]}>',
                'embeds': [
                    {
                        'title': f'Vault Request #{request_id}',
                        'description': f'{user.name} [{user.tid}] is requesting '
                                       f'{vault_balances["donations"][str(user.tid)]["money_balance"]} from the '
                                       f'faction vault. '
                                       f'To fulfill this request, enter `?f {request_id}` in this channel.',
                        'timestamp': datetime.datetime.utcnow().isoformat()
                    }
                ]
            }
        message = tasks.discordpost(f'channels/{vault_config["banking"]}/messages', payload=message_payload)

        withdrawal = WithdrawalModel(
            wid=request_id,
            amount=amount_requested if amount_requested != 'all' else vault_balances["donations"][str(user.tid)]["money_balance"],
            requester=user.tid,
            factiontid=user.factiontid,
            time_requested=utils.now(),
            fulfiller=0,
            time_fulfilled=0,
            withdrawal_message=message['id']
        )
        withdrawal.save()

        return jsonify({
            'id': request_id,
            'amount': withdrawal.amount,
            'requester': user.tid,
            'timerequested': withdrawal.time_requested,
            'withdrawalmessage': message['id']
        }), 200, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
    else:
        return jsonify({
            'code': 0,
            'name': 'UnknownFaction',
            'message': 'Server failed to fulfill the request. There was no faction stored with that faction ID.'
        }), 400, {
            'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
            'X-RateLimit-Remaining': client.get(key),
            'X-RateLimit-Reset': client.ttl(key)
        }
