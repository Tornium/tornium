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

from flask import render_template, request
from flask_login import current_user, fresh_login_required
from tornium_commons.models import FactionModel, ServerModel

from controllers.faction.decorators import aa_required, fac_required


@fresh_login_required
@fac_required
@aa_required
def bot(*args, **kwargs):
    faction: typing.Optional[FactionModel] = FactionModel.objects(tid=current_user.factiontid).first()

    if faction.guild == 0:
        return render_template(
            "faction/bot.html",
            guildid=faction.guild,
        )

    if request.method == "POST" and request.form.get("guildid") is not None:
        guild: ServerModel = ServerModel.objects(sid=request.form.get("guildid")).first()
        if guild is None:
            return render_template(
                "errors/error.html",
                title="Unknown Guild",
                error=f"The Discord server with ID {request.form.get('guildid')} could not be found.",
            )

        faction.guild = request.form.get("guildid")
        faction.save()

    return render_template(
        "faction/bot.html",
        guildid=faction.guild,
    )
