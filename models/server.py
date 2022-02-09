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

from models.servermodel import ServerModel
import tasks
import utils


class Server:
    def __init__(self, sid):
        """
        Retrieves the server from the database.

        :param sid: Discord server ID
        """

        server = utils.first(ServerModel.objects(sid=sid))
        if server is None:
            guild = tasks.discordget(f'guilds/{sid}')

            server = ServerModel(
                sid=sid,
                name=guild['name'],
                admins=[],
                prefix='?',
                config={'stakeouts': 0, 'assists': 0},
                factions=[],
                stakeoutconfig={'category': 0},
                userstakeouts=[],
                factionstakeouts=[],
                assistschannel=0
            )
            server.save()

        self.sid = sid
        self.name = server.name
        self.admins = server.admins
        self.prefix = server.prefix
        self.config = server.config

        self.factions = server.factions

        self.stakeout_config = server.stakeoutconfig
        self.user_stakeouts = server.userstakeouts
        self.faction_stakeouts = server.factionstakeouts

        self.assistschannel = server.assistschannel
