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

import datetime

from flask import render_template
from flask_login import current_user, login_required
from tornium_celery.tasks.faction import ORGANIZED_CRIMES
from tornium_commons.models import OrganizedCrime

from controllers.faction.decorators import fac_required


def crime_id_string(crime_id: int) -> str:
    return ORGANIZED_CRIMES.get(crime_id, "")


@login_required
@fac_required
def crimes_dashboard():
    now = datetime.datetime.utcnow()

    pending_crimes = (
        OrganizedCrime.select()
        .where(
            (OrganizedCrime.faction_tid == current_user.faction_id)
            & (OrganizedCrime.time_completed.is_null(True))
            & (OrganizedCrime.time_ready <= now)
            & (OrganizedCrime.canceled == False)
        )
        .order_by(-OrganizedCrime.time_ready)
        .limit(10)
    )
    in_process_crimes = (
        OrganizedCrime.select()
        .where((OrganizedCrime.faction_tid == current_user.faction_id) & (OrganizedCrime.time_ready > now))
        .order_by(OrganizedCrime.time_ready)
        .limit(10)
    )

    return render_template(
        "faction/crimes.html",
        pending_crimes=pending_crimes,
        in_progress_crimes=in_process_crimes,
        crime_id_string=crime_id_string,
        oc_types=ORGANIZED_CRIMES,
    )
