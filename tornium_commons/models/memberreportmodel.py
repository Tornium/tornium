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

from mongoengine import DictField, DynamicDocument, IntField, ListField, UUIDField


class MemberReportModel(DynamicDocument):
    rid = UUIDField(primary_key=True)
    created_at = IntField(required=True)
    last_updated = IntField(required=True)
    requested_by_user = IntField()  # None if not requested for a user
    requested_by_faction = IntField()  # None if not requested for a faction
    requested_data = ListField()
    status = IntField(default=0)

    # Report Status
    # 0: Not started
    # 1: In progress
    # 2: Completed
    # 999: Error

    faction_id = IntField(required=True)
    start_timestamp = IntField(required=True)
    end_timestamp = IntField(required=True)

    # TID: int -> PersonalStatModel.pid: int
    start_ps = DictField()
    end_ps = DictField()
