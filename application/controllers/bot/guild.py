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

import typing

from flask import render_template
from flask_login import current_user, fresh_login_required, login_required
from peewee import DoesNotExist
from tornium_commons.models import Faction, Server


@login_required
def dashboard():
    return render_template(
        "bot/dashboard.html",
        servers=Server.select(Server.name, Server.sid, Server.icon).where(Server.admins.contains(current_user.tid)),
    )


@fresh_login_required
def guild_dashboard(guild_id: str):
    try:
        guild: Server = (
            Server.select(
                Server.factions,
                Server.sid,
                Server.name,
                Server.admins,
            )
            .where(Server.sid == int(guild_id))
            .get()
        )
    except (ValueError, TypeError, DoesNotExist):
        return (
            render_template(
                "errors/error.html",
                title="Server Not Found",
                error="The server ID could not be located in the database.",
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

    factions: typing.List[Faction] = []

    for faction in guild.factions:
        try:
            faction: Faction = Faction.select(Faction.tid, Faction.name, Faction.guild).where(Faction.tid == faction).get()
            faction.aa_keys_missing = len(faction.aa_keys) == 0
            factions.append(faction)
        except DoesNotExist:
            continue

    return render_template(
        "bot/guild.html",
        server=guild,
        factions=factions,
        guildid=guild_id,
    )
