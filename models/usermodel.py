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

from mongoengine import DynamicDocument, IntField, StringField, DictField, ListField, BooleanField, FloatField


class UserModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField(default='')
    level = IntField(default=0)
    last_refresh = IntField(default=0)
    admin = BooleanField(default=False)
    key = StringField(default='')
    battlescore = FloatField(default=0.0)
    strength = FloatField(default=0.0)
    defense = FloatField(default=0.0)
    speed = FloatField(default=0.0)
    dexterity = FloatField(default=0.0)
    battlescore_update = IntField(default=0)

    discord_id = IntField(default=0)
    servers = ListField(default=[])  # List of discord servers where user is admin

    factionid = IntField(default=0)
    factionaa = BooleanField(default=False)
    chain_hits = IntField(default=0)

    status = StringField(default='')
    last_action = IntField(default=0)

    pro = BooleanField(default=False)
    pro_expiration = IntField(default=0)
