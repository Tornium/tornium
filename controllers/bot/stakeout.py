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

import datetime
import json

from flask import request, jsonify, render_template, redirect, flash
from flask_login import login_required, current_user

from models.faction import Faction
from models.factionstakeoutmodel import FactionStakeoutModel
from models.server import Server
from models.servermodel import ServerModel
from models.stakeout import Stakeout
from models.user import User
import tasks
import utils
from models.userstakeoutmodel import UserStakeoutModel


@login_required
def stakeouts_dashboard(guildid: str):
    server: ServerModel = utils.first(ServerModel.objects(sid=guildid))

    if server is None:
        return render_template('errors/error.html', title='Error', error='Server not found.'), 400
    elif server.sid not in current_user.servers:
        return render_template(
            'errors/error.html',
            title='Permission Denied',
            error=f'{current_user.name} [{current_user.tid}] is required to be an administrator '
                  f'of {server.name}.'
        ), 403

    if request.method == 'POST':
        if request.form.get('factionid') is not None:
            if int(request.form.get('factionid')) not in server.factionstakeouts:
                stakeout = Stakeout(int(request.form.get('factionid')), user=False, key=current_user.key,
                                    guild=int(guildid))
                stakeouts = server.factionstakeouts
                stakeouts.append(int(request.form.get('factionid')))
                server.factionstakeouts = list(set(stakeouts))

                if server.stakeoutconfig['category'] != 0:
                    payload = {
                        'name': f'faction-{stakeout.data["name"]}',
                        'type': 0,
                        'topic': f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                                 f'[{stakeout.data["ID"]}] by the Tornium bot.',
                        'parent_id': server.stakeoutconfig['category']
                    }  # TODO: Add permission overwrite: everyone write false
                else:
                    payload = {
                        'name': f'faction-{stakeout.data["name"]}',
                        'type': 0,
                        'topic': f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                                 f'[{stakeout.data["ID"]}] by the Tornium bot.'
                    }  # TODO: Add permission overwrite: everyone write false

                channel = tasks.discordpost(f'guilds/{guildid}/channels', payload=payload)

                db_stakeout = utils.first(FactionStakeoutModel.objects(tid=request.form.get('factionid')))
                db_stakeout.guilds[guildid]['channel'] = int(channel['id'])
                db_stakeout.save()

                message_payload = {
                    'embeds': [
                        {
                            'title': 'Faction Stakeout Creation',
                            'description': f'A stakeout of faction {stakeout.data["name"]} has been created in '
                                           f'{server.name}. This stakeout can be setup or removed in the '
                                           f'[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{server.sid}) by a '
                                           f'server administrator.',
                            'timestamp': datetime.datetime.utcnow().isoformat()
                        }
                    ]
                }
                tasks.discordpost(f'channels/{channel["id"]}/messages', payload=message_payload)
            else:
                flash(f'Faction ID {request.form.get("factionid")} is already being staked out in {server.name}.',
                      category='error')
        elif request.form.get('userid') is not None:
            if int(request.form.get('userid')) not in server.userstakeouts:
                stakeout = Stakeout(int(request.form.get('userid')), key=current_user.key, guild=int(guildid))
                server.userstakeouts.append(int(request.form.get('userid')))
                server.userstakeouts = list(set(server.userstakeouts))
                server.save()

                if server.stakeoutconfig['category'] != 0:
                    payload = {
                        'name': f'user-{stakeout.data["name"]}',
                        'type': 0,
                        'topic': f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                                 f'[{stakeout.data["player_id"]}] by the Tornium bot.',
                        'parent_id': server.stakeoutconfig['category']
                    }  # TODO: Add permission overwrite: everyone write false
                else:
                    payload = {
                        'name': f'user-{stakeout.data["name"]}',
                        'type': 0,
                        'topic': f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                                 f'[{stakeout.data["player_id"]}] by the Tornium bot.'
                    }  # TODO: Add permission overwrite: everyone write false

                channel = tasks.discordpost(f'guilds/{guildid}/channels', payload=payload)

                db_stakeout = utils.first(UserStakeoutModel.objects(tid=request.form.get('userid')))
                db_stakeout.guilds[guildid]['channel'] = int(channel['id'])
                db_stakeout.save()

                message_payload = {
                    'embeds': [
                        {
                            'title': 'User Stakeout Creation',
                            'description': f'A stakeout of user {stakeout.data["name"]} has been created in '
                                           f'{server.name}. This stakeout can be setup or removed in the '
                                           f'[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{server.sid}) by a '
                                           f'server administrator.',
                            'timestamp': datetime.datetime.utcnow().isoformat()
                        }
                    ]
                }
                tasks.discordpost(f'channels/{channel["id"]}/messages', payload=message_payload)
            else:
                flash(f'User ID {request.form.get("userid")} is already being staked out in {server.name}.',
                      category='error')

    return render_template('bot/stakeouts.html', guildid=guildid)


@login_required
def stakeouts(guildid: str, stype: int):
    server: ServerModel = utils.first(ServerModel.objects(sid=guildid))

    if server is None:
        return render_template('errors/error.html', title='Error', error='Server not found.'), 400
    elif server.sid not in current_user.servers:
        return render_template(
            'errors/error.html',
            title='Permission Denied',
            error=f'{current_user.name} [{current_user.tid}] is required to be an administrator '
                  f'of {server.name}.'
        ), 403

    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    stakeouts = []

    if stype == 0:  # user
        filtered = len(server.userstakeouts)
        for stakeout in server.userstakeouts:
            stakeout = Stakeout(int(stakeout), key=current_user.key)
            stakeouts.append(
                [stakeout.tid, stakeout.guilds[guildid]['keys'],
                 utils.rel_time(datetime.datetime.fromtimestamp(stakeout.last_update))]
            )
    elif stype == 1:  # faction
        filtered = len(server.factionstakeouts)
        for stakeout in server.factionstakeouts:
            stakeout = Stakeout(int(stakeout), user=False, key=current_user.key)
            stakeouts.append(
                [stakeout.tid, stakeout.guilds[guildid]['keys'],
                 utils.rel_time(datetime.datetime.fromtimestamp(stakeout.last_update))]
            )
    else:
        filtered = 0

    stakeouts = stakeouts[start:start + length]
    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': len(server.userstakeouts) + len(server.factionstakeouts),
        'recordsFiltered': filtered,
        'data': stakeouts
    }
    return data


@login_required
def stakeout_data(guildid: str):
    server: ServerModel = utils.first(ServerModel.objects(sid=guildid))

    if server is None:
        return render_template('errors/error.html', title='Error', error='Server not found.'), 400
    elif server.sid not in current_user.servers:
        return render_template(
            'errors/error.html',
            title='Permission Denied',
            error=f'{current_user.name} [{current_user.tid}] is required to be an administrator '
                  f'of {server.name}.'
        ), 403

    faction = request.args.get('faction')
    user = request.args.get('user')

    if (not faction and not user) or (faction and user):
        raise Exception  # TODO: make exception more descriptive

    if faction:
        if int(faction) not in server.factionstakeouts:
            raise Exception

        stakeout = Stakeout(faction, user=False)

        return render_template('bot/factionstakeoutmodal.html',
                               faction=f'{Faction(int(faction), key=current_user.key).name} [{faction}]',
                               lastupdate=utils.rel_time(datetime.datetime.fromtimestamp(stakeout.last_update)),
                               keys=stakeout.guilds[guildid]['keys'],
                               guildid=guildid,
                               tid=faction,
                               armory=(int(faction) not in Server(guildid).factions or
                                       Faction(faction).guild != int(guildid)))
    elif user:
        if int(user) not in server.userstakeouts:
            raise Exception

        stakeout = Stakeout(user)
        return render_template('bot/userstakeoutmodal.html',
                               user=f'{User(int(user), key=current_user.key).name} [{user}]',
                               lastupdate=utils.rel_time(datetime.datetime.fromtimestamp(stakeout.last_update)),
                               keys=stakeout.guilds[guildid]['keys'],
                               guildid=guildid,
                               tid=user)


@login_required
def stakeout_update(guildid):
    server: ServerModel = utils.first(ServerModel.objects(sid=guildid))

    if server is None:
        return render_template('errors/error.html', title='Error', error='Server not found.'), 400
    elif server.sid not in current_user.servers:
        return render_template(
            'errors/error.html',
            title='Permission Denied',
            error=f'{current_user.name} [{current_user.tid}] is required to be an administrator '
                  f'of {server.name}.'
        ), 403

    action = request.args.get('action')
    faction = request.args.get('faction')
    user = request.args.get('user')
    value = request.args.get('value')

    if action not in ['remove', 'addkey', 'removekey', 'enable', 'disable', 'category']:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}
    elif faction and user:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}

    if action == 'remove':
        server = utils.first(ServerModel.objects(sid=guildid))

        if faction is not None:
            server.factionstakeouts.remove(int(faction))

            stakeout = utils.first(FactionStakeoutModel.objects(tid=faction))
            stakeout.guilds.pop(str(guildid))

            if len(stakeout.guilds) == 0:
                stakeout.delete()
            else:
                stakeout.save()

            tasks.discorddelete(f'channels/{stakeout.guilds[guildid]["channel"]}')
        elif user is not None:
            server.userstakeouts.remove(int(user))

            stakeout = utils.first(UserStakeoutModel.objects(tid=user))
            stakeout.guilds.pop(str(guildid))

            if len(stakeout.guilds) == 0:
                stakeout.delete()
            else:
                stakeout.save()

            tasks.discorddelete(f'channels/{stakeout.guilds[guildid]["channel"]}')

        server.save()
    elif action == 'addkey':
        if faction is not None and value not in ['territory', 'members', 'memberstatus', 'memberactivity', 'armory',
                                                 'assault', 'armorydeposit']:
            return jsonify({'error': f'Faction is set to {faction} for a key that doesn\'t allow a faction '
                                     f'ID to be passed.'}), 400
        elif user is not None and value not in ['level', 'status', 'flyingstatus', 'online', 'offline']:
            return jsonify({'error': f'User is set to {user} for a key that doesn\'t allow a user '
                                     f'ID to be passed.'}), 400
        elif value == 'armory' and (int(faction) not in Server(guildid).factions or
                                    Faction(faction).guild != int(guildid)):
            return jsonify({'error': f'This requires the faction to be in the list of factions in the server.'}), 400

        if user is not None:
            stakeout = utils.first(UserStakeoutModel.objects(tid=user))
        else:
            stakeout = utils.first(FactionStakeoutModel.objects(tid=faction))

        if value in stakeout.guilds[guildid]['keys']:
            return jsonify({'error': f'Value {value} is already in {guildid}\'s list of keys.'}), 400

        stakeout.guilds[guildid]['keys'].append(value)
        stakeout.save()
    elif action == 'removekey':
        if faction is not None and value not in ['territory', 'members', 'memberstatus', 'memberactivity', 'armory',
                                                 'assault', 'armorydeposit']:
            return jsonify({'error': f'Faction is set to {faction} for a key that doesn\'t allow a faction '
                                     f'ID to be passed.'}), 400
        elif user is not None and value not in ['level', 'status', 'flyingstatus', 'online', 'offline']:
            return jsonify({'error': f'User is set to {user} for a key that doesn\'t allow a user '
                                     f'ID to be passed.'}), 400

        if user is not None:
            stakeout = utils.first(UserStakeoutModel.objects(tid=user))
        else:
            stakeout = utils.first(FactionStakeoutModel.objects(tid=faction))

        if value not in stakeout.guilds[guildid]['keys']:
            return jsonify({'error': f'Value {value} is not in {guildid}\'s list of keys.'}), 400

        stakeout.guilds[guildid]['keys'].remove(value)
        stakeout.save()
    elif action == 'enable':
        server = utils.first(ServerModel.objects(sid=guildid))
        server.config['stakeouts'] = 1
        server.save()
    elif action == 'disable':
        server = utils.first(ServerModel.objects(sid=guildid))
        server.config['stakeouts'] = 0
        server.save()
    elif action == 'category':
        server = utils.first(ServerModel.objects(sid=guildid))
        server.stakeoutconfig['category'] = int(value)
        server.save()

    if request.method == 'GET':
        return redirect(f'/bot/stakeouts/{guildid}')
    else:
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
