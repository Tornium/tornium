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

from flask import render_template, request
from flask_login import current_user, login_required
from huey.exceptions import TaskException

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
