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

from flask import request, jsonify, redirect
from flask_login import login_required

from models.servermodel import ServerModel
import utils


@login_required
def assists_update(guildid):
    action = request.args.get('action')
    value = request.args.get('value')

    if action not in ['enable', 'disable', 'channel']:
        return jsonify({
            'success': False
        }), 400, jsonify({
            'ContentType': 'application/json'
        })

    if action == 'enable':
        server = utils.first(ServerModel.objects(sid=guildid))
        server.config['assists'] = 1
        server.save()
    elif action == 'disable':
        server = utils.first(ServerModel.objects(sid=guildid))
        server.config['assists'] = 0
        server.save()
    elif action == 'channel':
        server = utils.first(ServerModel.objects(sid=guildid))
        server.assistschannel = int(value)
        server.save()

    if request.method == 'GET':
        return redirect(f'/bot/dashboard/{guildid}')
    else:
        return {
            'success': True
        }, 200, {
            'ContentType': 'application/json'
        }
