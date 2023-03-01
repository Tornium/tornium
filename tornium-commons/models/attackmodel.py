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

from mongoengine import BooleanField, DictField, DynamicDocument, FloatField, IntField, StringField


class AttackModel(DynamicDocument):
    code = StringField(primary_key=True)
    timestamp_start = IntField()
    timestamp_ended = IntField()
    attacker = IntField(required=True)
    attacker_faction = IntField()
    defender = IntField(required=True)
    defender_faction = IntField()
    result = IntField(required=True)
    stealth = BooleanField(required=True)
    respect = FloatField()
    chain = IntField()
    raid = IntField()
    ranked_war = IntField()
    modifiers = DictField()
