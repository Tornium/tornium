# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

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
