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

import datetime

from flask import render_template
from flask_login import current_user, login_required
from peewee import DoesNotExist
from tornium_commons.models import (
    EliminationTeam,
    Server,
    ServerVerificationEliminationConfig,
)


@login_required
def verify_dashboard(guild_id: int):
    try:
        guild: Server = (
            Server.select(
                Server.sid,
                Server.verify_enabled,
                Server.verify_template,
                Server.auto_verify_enabled,
                Server.gateway_verify_enabled,
                Server.faction_verify,
                Server.admins,
            )
            .where(Server.sid == guild_id)
            .get()
        )
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Guild Not Found",
                error="No Discord server could be located with the passed guild ID",
            ),
            400,
        )

    if current_user.tid not in guild.admins:
        return (
            render_template(
                "errors/error.html",
                title="Permission Denied",
                error="Only server admins are able to access this page, and you do not have this permission.",
            ),
            403,
        )

    year = datetime.datetime.utcnow().year
    elimination_teams_ids = [
        (team.guid, team.name) for team in EliminationTeam.select().where(EliminationTeam.year == year)
    ]
    configs = ServerVerificationEliminationConfig.select().where(
        (ServerVerificationEliminationConfig.team.in_([t[0] for t in elimination_teams_ids]))
        & (ServerVerificationEliminationConfig.server_id == guild_id)
    )
    existing_elimination_team_configurations = {config.team_id: config for config in configs}
    elimination_team_configurations = {
        team[0]: {"name": team[1], "config": existing_elimination_team_configurations.get(team[0])}
        for team in elimination_teams_ids
    }
    print(elimination_team_configurations)

    return render_template(
        "bot/verify.html", guild=guild, elimination_team_configurations=elimination_team_configurations
    )
