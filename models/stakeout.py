# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import time

from flask_login import current_user
from tornium_celery.tasks.api import tornget
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.models import FactionStakeoutModel, UserStakeoutModel


class Stakeout:
    def __init__(self, tid, guild=None, user=True, key=""):
        if user:
            stakeout = UserStakeoutModel.objects(tid=tid).first()
        else:
            stakeout = FactionStakeoutModel.objects(tid=tid).first()

        if stakeout is None:
            now = int(time.time())
            guilds = {} if guild is None else {str(guild): {"keys": [], "channel": 0}}

            if user:
                try:
                    data = tornget(f"user/{tid}?selections=", key if key != "" else current_user.key)
                except (TornError, NetworkingError):
                    data = {}

                stakeout = UserStakeoutModel(tid=tid, data=data, guilds=guilds, last_update=now)

            else:
                try:
                    data = tornget(f"faction/{tid}?selections=", key if key != "" else current_user.key)
                except (TornError, NetworkingError):
                    data = {}

                stakeout = FactionStakeoutModel(tid=tid, data=data, guilds=guilds, last_update=now)

            stakeout.save()
        elif guild not in stakeout.guilds and guild is not None:
            stakeout.guilds[str(guild)] = {"keys": [], "channel": 0}
            stakeout.save()

        self.tid = tid
        self.stype = 0 if user else 1  # 0 = user; 1 = faction
        self.guilds = stakeout.guilds
        self.last_update = stakeout.last_update
        self.data = stakeout.data
