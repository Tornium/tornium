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

from flask import render_template, request
from flask_login import current_user, fresh_login_required
from tornium_commons.models import Server

from controllers.faction.decorators import aa_required, fac_required


@fresh_login_required
@fac_required
@aa_required
def bot(*args, **kwargs):
    if request.method == "POST" and request.form.get("guildid") is not None:
        try:
            guild_id = int(request.form["guildid"])
        except (KeyError, ValueError, TypeError):
            return (
                render_template(
                    "errors/error.html",
                    title="Invalid Guild",
                    error=f"The Discord server ID {request.form.get('guildid')} is not valid.",
                ),
                400,
            )

        if Server.select().where(Server.sid == guild_id).exists():
            return render_template(
                "errors/error.html",
                title="Unknown Guild",
                error=f"The Discord server with ID {request.form.get('guildid')} could not be found.",
            )

        current_user.faction.guild = guild_id
        current_user.faction.save()

    return render_template(
        "faction/bot.html",
        guildid=current_user.faction.guild_id,
    )
