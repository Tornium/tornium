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
from flask_login import current_user, fresh_login_required, login_required
from tornium_commons.models import FactionModel, ServerModel


@login_required
def dashboard():
    return render_template(
        "bot/dashboard.html", servers=list(ServerModel.objects(admins=current_user.tid).only("name", "sid", "icon"))
    )


@fresh_login_required
def guild_dashboard(guildid: str):
    server: typing.Optional[ServerModel] = ServerModel.objects(sid=guildid).first()

    if server is None:
        return (
            render_template(
                "errors/error.html",
                title="Server Not Found",
                error="The server ID could not be located in the database.",
            ),
            400,
        )
    elif current_user.tid not in server.admins:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error="Only server admins are able to access this page, and you do not have this permission.",
            ),
            403,
        )

    factions: typing.List[FactionModel] = []
    assist_factions = []

    faction: typing.Union[int, FactionModel]
    for faction in server.factions:
        faction: typing.Optional[FactionModel] = FactionModel.objects(tid=faction).only("tid", "name", "guild").first()

        if faction is None:
            continue

        factions.append(faction)

    for faction in server.assist_factions:
        faction: typing.Optional[FactionModel] = (
            FactionModel.objects(tid=faction)
            .only(
                "tid",
                "name",
            )
            .first()
        )

        if faction is None:
            pass

        assist_factions.append(faction)

    return render_template(
        "bot/guild.html",
        server=server,
        factions=factions,
        guildid=guildid,
        assist_factions=assist_factions,
    )
