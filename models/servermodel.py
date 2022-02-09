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

from mongoengine import DynamicDocument, IntField, StringField, DictField, ListField, LongField


class ServerModel(DynamicDocument):
    sid = LongField(primary_key=True)
    name = StringField(default='')
    admins = ListField(default=[])  # List of admin ids
    prefix = StringField(default='?')
    config = DictField(default={'stakeouts': 0, 'assists': 0})  # Dictionary of server configurations

    factions = ListField(default=[])  # List of factions in server

    stakeoutconfig = DictField(default={'category': 0})  # Dictionary of stakeout configurations for the server
    userstakeouts = ListField(default=[])  # List of staked-out users
    factionstakeouts = ListField(default=[])  # List of staked-out factions

    assistschannel = IntField(default=0)
