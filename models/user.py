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

import math

from flask_login import UserMixin, current_user

from models.usermodel import UserModel
import tasks
import utils


class User(UserMixin):
    def __init__(self, tid, key=''):
        """
        Retrieves the user from the database.

        :param tid: Torn user ID
        """

        user = utils.first(UserModel.objects(_id=tid))
        if user is None:
            user = UserModel(
                tid=tid,
                name='',
                level=0,
                last_refresh=0,
                admin=False,
                key=key,
                battlescore=0,
                battlescore_update=0,
                discord_id=0,
                servers=[],
                factionid=0,
                factionaa=False,
                chain_hits=0,
                status='',
                last_action=0
            )
            user.save()

        self.tid = tid
        self.name = user.name
        self.level = user.level
        self.last_refresh = user.last_refresh
        self.admin = user.admin
        self.key = user.key
        self.battlescore = user.battlescore
        self.battlescore_update = user.battlescore_update

        self.discord_id = user.discord_id
        self.servers = user.servers

        self.factiontid = user.factionid
        self.aa = user.factionaa
        self.chain_hits = user.chain_hits

        self.status = user.status
        self.last_action = user.last_action

        self.pro = user.pro
        self.pro_expiration = user.pro_expiration

    def refresh(self, key=None, force=False):
        now = utils.now()
        
        if force or (now - self.last_refresh) > 1800:
            if self.key != "":
                key = self.key
            elif key is None:
                key = current_user.key
                if key == '':
                    raise Exception  # TODO: Make exception more descriptive

            if key == self.key:
                user_data = tasks.tornget(f'user/?selections=profile,battlestats,discord', key)
            else:
                user_data = tasks.tornget(f'user/{self.tid}?selections=profile,discord', key)

            user = utils.first(UserModel.objects(tid=self.tid))
            user.factionid = user_data['faction']['faction_id']
            user.name = user_data['name']
            user.last_refresh = now
            user.status = user_data['last_action']['status']
            user.last_action = user_data['last_action']['timestamp']
            user.level = user_data['level']
            user.discord_id = user_data['discord']['discordID'] if user_data['discord']['discordID'] != '' else 0

            if key == self.key:
                user.battlescore = math.sqrt(user_data['strength']) + math.sqrt(user_data['speed']) + \
                                   math.sqrt(user_data['speed']) + math.sqrt(user_data['dexterity'])
                user.battlescore_update = now

            user.save()

            self.name = user_data['name']
            self.factiontid = user_data['faction']['faction_id']
            self.last_refresh = now
            self.status = user_data['last_action']['status']
            self.last_action = user_data['last_action']['timestamp']
            self.level = user_data['level']
            self.battlescore = user.battlescore
            self.battlescore_update = now
            self.discord_id = user.discord_id

    def faction_refresh(self):
        user = utils.first(UserModel.objects(tid=self.tid))

        try:
            tasks.tornget(f'faction/?selections=positions', self.key)
        except:
            self.aa = False
            user.factionaa = False
            return

        self.aa = True
        user.factionaa = True

        user.save()

    def get_id(self):
        return self.tid
    
    def is_aa(self):
        return self.aa

    def set_key(self, key: str):
        user = utils.first(UserModel.objects(tid=self.tid))
        user.key = key
        self.key = key
        user.save()
