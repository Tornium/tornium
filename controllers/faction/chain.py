# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template, request
from flask_login import current_user, login_required

from models.faction import Faction
from models.factionmodel import FactionModel
import tasks
import utils


@login_required
def chain():
    faction = Faction(current_user.factiontid)

    if request.method == 'POST':
        faction_model = utils.first(FactionModel.objects(tid=current_user.factiontid))

        if request.form.get('odchannel') is not None:
            try:
                channel = tasks.discordget(f'channels/{request.form.get("odchannel")}')
                channel = channel(blocking=True)
            except TaskException as e:
                e = str(e)
                if 'DiscordError' in e:
                    return utils.handle_discord_error(e)
                elif 'NetworkingError' in e:
                    return render_template('errors/error.html', title='Discord Networking Error',
                                           error=f'The Discord API has responded with HTTP error code '
                                                 f'{utils.remove_str(e)}.')
                else:
                    raise e

            config = faction_model.chainconfig
            config['odchannel'] = int(channel['id'])
            faction_model.save()
        elif (request.form.get('odenabled') is not None) ^ (request.form.get('oddisabled') is not None):
            config = faction_model.chainconfig

            if request.form.get('odenabled') is not None:
                config['od'] = 1
                faction_model.save()
            if request.form.get('oddisabled') is not None:
                config['od'] = 0
                faction_model.save()

    return render_template('faction/chain.html', faction=faction)
