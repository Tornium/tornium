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

import os
import json

from flask import render_template, request, jsonify
from flask_login import login_required, current_user

from models.faction import Faction
from models.schedule import Schedule
from models.schedulemodel import ScheduleModel
from models.user import User
import utils


@login_required
def schedule():
    if request.args.get('uuid') is not None and request.args.get('watchers') is None:
        schedule = Schedule(request.args.get('uuid'), factiontid=current_user.factiontid)
        return render_template('faction/schedulemodal.html', sid=schedule.name)
    elif request.args.get('uuid') is not None and request.args.get('watchers') is not None:
        schedule = Schedule(request.args.get('uuid'), factiontid=current_user.factiontid)
        data = []

        for tid, userdata in schedule.activity.items():
            modified_userdata = []

            for activity in userdata:
                activity = [int(activity.split('-')[0]), int(activity.split('-')[1])]
                activity[0] = utils.torn_timestamp(activity[0])
                activity[1] = utils.torn_timestamp(activity[1])
                modified_userdata.append(f'{activity[0]} to {activity[1]}')

            data.append([f'{User(tid).name} [{tid}]', modified_userdata, schedule.weight[tid]])

        return jsonify(data)

    return render_template('faction/schedule.html', key=current_user.key)


@login_required
def schedule_data():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    faction = Faction(current_user.factiontid)
    schedules = []

    for schedule in ScheduleModel.objects(factiontid=faction.tid):
        with open(f'{os.getcwd()}/schedule/{schedule.uuid}.json') as file:
            data = json.load(file)
            schedules.append([
                schedule.uuid,
                data['name'],
                utils.torn_timestamp(data['timecreated']),
                utils.torn_timestamp(data['timeupdated'])
            ])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': ScheduleModel.objects().count(),
        'recordsFiltered': len(schedules),
        'data': schedules[start:start + length]
    }
    return data
