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

from mongoengine import DynamicDocument, IntField, StringField, DictField, ListField


class FactionModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField(default='')
    respect = IntField(default=0)
    capacity = IntField(default=0)
    leader = IntField(default=0)
    coleader = IntField(default=0)

    keys = ListField(default=[])  # String of list of keys

    last_members = IntField(default=0)  # Time of last members update

    guild = IntField(default=0)  # Guild ID of the faction's guild
    config = DictField(default={'vault': 0, 'stats': 1})  # Dictionary of faction's bot configuration
    vaultconfig = DictField(default={'banking': 0, 'banker': 0, 'withdrawal': 0})  # Dictionary of vault configuration

    statconfig = DictField(default={'global': 0})  # Dictionary of target config

    chainconfig = DictField(default={'od': 0, 'odchannel': 0})  # Dictionary of chain config
    chainod = DictField(default={})  # Dictionary of faction member overdoses

    groups = ListField(default=[])
