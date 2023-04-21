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

from mongoengine import DictField, DynamicDocument, IntField, ListField, StringField


class FactionModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField(default="")
    respect = IntField(default=0)
    capacity = IntField(default=0)
    leader = IntField(default=0)
    coleader = IntField(default=0)
    aa_keys = ListField(default=[])

    last_members = IntField(default=0)  # Time of last members update
    last_attacks = IntField(default=0)

    guild = IntField(default=0)  # Guild ID of the faction's guild
    config = DictField(default={"stats": 1})  # Dictionary of faction's bot configuration

    statconfig = DictField(default={"global": 0})  # Dictionary of target config

    od_channel = IntField(default=0)
    chainod = DictField(default={})  # Dictionary of faction member overdoses
