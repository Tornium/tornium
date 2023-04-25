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

from mongoengine import (
    DictField,
    DynamicDocument,
    IntField,
    ListField,
    LongField,
    StringField,
)


class ServerModel(DynamicDocument):
    sid = LongField(primary_key=True)
    name = StringField(default="")
    admins = ListField(default=[])  # List of admin ids
    config = DictField(default={"stakeouts": 0, "verify": 0})  # Dictionary of server configurations
    icon = StringField(default="")  # icon hash

    factions = ListField(default=[])  # List of factions in server

    stakeoutconfig = DictField(default={"category": 0})  # Dictionary of stakeout configurations for the server
    userstakeouts = ListField(default=[])  # List of staked-out users
    factionstakeouts = ListField(default=[])  # List of staked-out factions

    verify_template = StringField(default="{{ name }} [{{ tid }}]")
    verified_roles = ListField(default=[])
    exclusion_roles = ListField(default=[])
    faction_verify = DictField(default={})
    verify_log_channel = IntField(default=0)

    retal_config = DictField(default={})  # Configuration of retals for the server

    banking_config = DictField(default={})  # Configuration for faction banking

    assistschannel = IntField(default=0)
    assist_factions = ListField(default=[])  # List of factions that can send assists to the server
    assist_mod = IntField(default=0)  # 0: Everyone; 1: Whitelist; 2: Blacklist

    oc_config = DictField(default={})

    stocks_channel = IntField(default=0)  # 0 = disabled
    stocks_config = DictField(default={})
