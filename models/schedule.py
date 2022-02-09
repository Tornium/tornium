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

import itertools
import json
import math
import os

from flask_login import current_user

from models.schedulemodel import ScheduleModel
from models.user import User
import utils


# 10-12 refers to starting at 10 ending at 12 or [10, 12) mathematically

class Schedule:
    def __init__(self, uuid, factiontid=None):
        schedule = utils.first(ScheduleModel.objects(uuid=uuid))
        
        if schedule is None and factiontid is None:
            raise Exception
        elif schedule is None:
            schedule = ScheduleModel(
                uuid=uuid,
                factiontid=factiontid,
                name=uuid,
                timecreated=utils.now(),
                timeupdated=utils.now(),
                activity={},
                weight={},
                schedule={},
                fromts=0,
                tots=0
            )
            schedule.save()
        
        self.uuid = uuid
        self.factiontid = schedule.factiontid

        if current_user.factiontid != self.factiontid and factiontid != self.factiontid:
            raise Exception

        self.name = schedule.name
        self.time_created = schedule.timecreated
        self.time_updated = schedule.timeupdated
        self.activity = schedule.activity
        self.weight = schedule.weight
        self.schedule = schedule.schedule
        self.fromts = schedule.fromts
        self.tots = schedule.tots

    def add_activity(self, tid, activity=None):
        if activity is None:
            if tid in self.activity:
                raise Exception
            self.activity[tid] = []
        else:
            if tid in self.activity:
                self.activity[tid].append(activity)
            else:
                self.activity[tid] = [activity]

        schedule = utils.first(ScheduleModel.objects(uuid=self.uuid))
        schedule.activity = self.activity
        schedule.save()

    def remove_user(self, tid):
        self.activity.pop(tid, None)
        self.weight.pop(tid, None)
        schedule = utils.first(ScheduleModel.objects(uuid=self.uuid))
        schedule.activity = self.activity
        schedule.weight = self.weight
        schedule.save()

    def set_weight(self, tid, weight):
        self.weight[tid] = weight
        schedule = utils.first(ScheduleModel.objects(uuid=self.uuid))
        schedule.weight = self.weight
        schedule.save()

    def delete(self):
        schedule = utils.first(ScheduleModel.objects(uuid=self.uuid))
        schedule.delete()

    def generate(self):
        users = {}

        def __calculate_interval_weight(fromts, tots, tid):
            if tid in users:
                user = users[tid]
            else:
                user = User(tid)
                users[tid] = user

            return math.log10(user.chain_hits) * self.weight[tid] * math.pow(math.e, (
                - ((tots - fromts) / 3600 - 2) ** 2) / (2 * 0.5 ** 2)) / (0.5 * math.sqrt(2 * math.pi))

        intervals = []
        temp_schedule = {
            'primary': {},
            'backup': {}
        }
        temperature = 0

        for tid, user_intervals in self.activity.items():
            for interval in user_intervals:
                fromts = int(interval.split('-')[0])
                tots = int(interval.split('-')[1])

                if fromts < self.fromts or tots > self.tots:
                    continue

                intervals.append([fromts, tots, tid])

        # Begin Timsort
        # 32 is size of each slice
        for i in range(0, len(intervals), 32):
            left = i
            right = min((i + 32 - 1), len(intervals) - 1)

            for j in range(left + 1, right + 1):
                key_item = intervals[j]
                k = j - 1

                while k >= left and intervals[k] > key_item:
                    intervals[k + 1] = intervals[k]

                intervals[k + 1] = key_item

        size = 32
        while size < len(intervals):
            for start in range(0, len(intervals), size * 2):
                midpoint = start + size - 1
                end = min((start + size * 2 - 1), (len(intervals) - 1))

                if len(intervals[start:midpoint + 1]) == 0:
                    merged_array = intervals[midpoint + 1:end + 1]
                elif len(intervals[midpoint + 1:end + 1]) == 0:
                    merged_array = intervals[start:midpoint + 1]
                else:
                    merged_array = []
                    index_left = 0
                    index_right = 0

                    while len(merged_array) < len(intervals[start:midpoint + 1]):
                        if intervals[start:midpoint + 1][index_left] <= intervals[midpoint + 1:end + 1][index_right]:
                            merged_array.append(intervals[start:midpoint + 1][index_left])
                            index_left += 1
                        else:
                            merged_array.append(intervals[midpoint + 1:end + 1][index_right])
                            index_right += 1

                        if index_right == len(intervals[midpoint + 1:end + 1]):
                            merged_array += intervals[start:midpoint + 1][index_left:]
                            break
                        elif index_left == len(intervals[start:midpoint + 1]):
                            merged_array += intervals[midpoint + 1:end + 1][index_right:]
                            break

                intervals[start:start + len(merged_array)] = merged_array

            size *= 2

        # End Timsort

        for length in range(len(intervals) + 1):
            for permutation in itertools.permutations(intervals, length):
                primary = permutation
                secondary = permutation

        return self.schedule
