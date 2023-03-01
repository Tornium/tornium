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

from mongoengine import BooleanField, DynamicDocument, IntField, ListField


class OCModel(DynamicDocument):
    meta = {"indexes": ["factiontid", ("factiontid", "ocid")]}

    factiontid = IntField(required=True)
    ocid = IntField(required=True)
    crime_id = IntField(required=True)
    participants = ListField(required=True)
    time_started = IntField(required=True)
    time_ready = IntField(required=True)
    time_completed = IntField(required=True)  # 0 if not initiated yet
    planned_by = IntField(required=True)
    initiated_by = IntField(default=0)  # 0 if not initiated yet
    money_gain = IntField(default=0)  # 0 if not initiated yet
    respect_gain = IntField(default=0)  # 0 if not initiated yet
    delayers = ListField(default=[])
    notified = BooleanField(default=False)
