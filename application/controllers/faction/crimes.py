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

from flask import render_template
from flask_login import current_user, login_required
from tornium_commons.models import OrganizedCrimeTeam

from controllers.faction.decorators import fac_required, manage_crimes_required


@login_required
@fac_required
@manage_crimes_required
def crimes(*args, **kwargs):
    teams = OrganizedCrimeTeam.select().where(OrganizedCrimeTeam.faction_id == current_user.faction_id)
    return render_template("faction/crimes.html", teams=teams.limit(10), team_count=teams.count())
