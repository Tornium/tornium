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
    BooleanField,
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
    config = DictField(default={"verify": 0})  # Dictionary of server configurations
    icon = StringField(default="")  # icon hash

    factions = ListField(default=[])  # List of factions in server

    verify_template = StringField(default="{{ name }} [{{ tid }}]")
    verified_roles = ListField(default=[])
    exclusion_roles = ListField(default=[])
    faction_verify = DictField(default={})
    verify_log_channel = IntField(default=0)

    retal_config = DictField(default={})  # Configuration of retals for the server

    banking_config = DictField(default={})  # Configuration for faction banking

    # Configuration for armory tracking
    # per faction: {
    #     str(faction_id): {
    #         "channel": int(channel_id)
    #         "roles": [list of int(roles)]
    #         "items": {
    #             str(item_id): int(minimum_quantity)
    #         }
    #     }
    # }
    armory_config = DictField(default={})
    armory_enabled = BooleanField(default=False)

    assistschannel = IntField(default=0)
    assist_factions = ListField(default=[])  # List of factions that can send assists to the server
    assist_smoker_roles = ListField(default=[])
    assist_tear_roles = ListField(default=[])
    assist_l0_roles = ListField(default=[])  # 500m+
    assist_l1_roles = ListField(default=[])  # 1b+
    assist_l2_roles = ListField(default=[])  # 2b+
    assist_l3_roles = ListField(default=[])  # 5b+

    oc_config = DictField(default={})

    stocks_channel = IntField(default=0)  # 0 = disabled
    stocks_config = DictField(default={})
