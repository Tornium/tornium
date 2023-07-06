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

from mongoengine import BooleanField, DictField, DynamicDocument, DynamicField, IntField


class NotificationModel(DynamicDocument):
    ###############
    # Notification types
    #
    # 0: stocks price reach
    # 1: user stakeout
    # 2: faction stakeout
    # 3: item notif
    ###############

    invoker = IntField(required=True)  # TID of notification creator
    time_created = IntField(required=True)

    recipient = IntField(required=True)
    recipient_guild = IntField()  # 0: DM
    recipient_type = IntField(required=True)  # 0: DM; 1: channel

    ntype = IntField(required=True)
    target = DynamicField(required=True)
    persistent = BooleanField(default=False)
    value = DynamicField()
    options = DictField(default={})
