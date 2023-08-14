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

import typing

from flask import render_template
from flask_login import current_user, login_required
from tornium_commons.models import FactionModel

from controllers.faction.decorators import fac_required


@login_required
@fac_required
def chain(*args, **kwargs):
    faction: typing.Optional[FactionModel] = FactionModel.objects(tid=current_user.factiontid).first()

    return render_template("faction/chain.html", guild_id=0 if faction.guild is None else faction.guild)
