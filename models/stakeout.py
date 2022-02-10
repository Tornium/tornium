# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

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
