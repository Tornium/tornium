# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from flask import abort, render_template
from flask_login import login_required

from controllers.faction.decorators import aa_required, fac_required


@login_required
@fac_required
def faction_calendar(*args, **kwargs):
    return render_template("faction/calendar/calendar.html")


@login_required
@fac_required
@aa_required
def create_calendar_event(*args, **kwargs):
    return render_template("faction/calendar/new-event.html")


@login_required
@fac_required
@aa_required
def create_specific_event(event_type: str, *args, **kwargs):
    if event_type not in ("steadfast"):
        abort(404)

    return render_template(f"faction/calendar/new-{event_type}-event.html")
