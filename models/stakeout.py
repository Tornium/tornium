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

from flask_login import current_user

from models.factionstakeoutmodel import FactionStakeoutModel
from models.userstakeoutmodel import UserStakeoutModel
import tasks
import utils


class Stakeout:
    def __init__(self, tid, guild=None, user=True, key=''):
        if user:
            stakeout = utils.first(UserStakeoutModel.objects(tid=tid))
        else:
            stakeout = utils.first(FactionStakeoutModel.objects(tid=tid))

        if stakeout is None:
            now = utils.now()
            guilds = {} if guild is None else {str(guild): {'keys': [], 'channel': 0}}

            if user:
                try:
                    data = tasks.tornget(f'user/{tid}?selections=', key if key != '' else current_user.key)
                except:
                    data = {}

                stakeout = UserStakeoutModel(
                    tid=tid,
                    data=data,
                    guilds=guilds,
                    last_update=now
                )

            else:
                try:
                    data = tasks.tornget(f'faction/{tid}?selections=', key if key != '' else current_user.key)
                except:
                    data = {}

                stakeout = FactionStakeoutModel(
                    tid=tid,
                    data=data,
                    guilds=guilds,
                    last_update=now
                )

            stakeout.save()
        elif guild not in stakeout.guilds and guild is not None:
            stakeout.guilds[str(guild)] = {
                'keys': [],
                'channel': 0
            }
            stakeout.save()

        self.tid = tid
        self.stype = 0 if user else 1  # 0 = user; 1 = faction
        self.guilds = stakeout.guilds
        self.last_update = stakeout.last_update
        self.data = stakeout.data
