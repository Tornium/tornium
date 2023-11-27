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

from flask import render_template
from flask_login import current_user, login_required

from controllers.faction.decorators import fac_required


@login_required
@fac_required
def chain(*args, **kwargs):
    return render_template(
        "faction/chain.html",
        guild_id=0 if current_user.faction.guild_id is None else current_user.faction.guild_id,
    )
