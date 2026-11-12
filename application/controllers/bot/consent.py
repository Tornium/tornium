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
from flask_login import current_user, fresh_login_required
from peewee import DoesNotExist
from tornium_commons.models import OAuthClientResourceConsent, Server


@fresh_login_required
def consent(guild_id: int, *args, **kwargs):
    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
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

    consents: typing.List[OAuthClientResourceConsent] = [
        c
        for c in OAuthClientResourceConsent.select().where(
            (OAuthClientResourceConsent.server == guild.sid) & (OAuthClientResourceConsent.revoked_at.is_null(True))
        )
    ]
    can_revoke_consent = current_user.faction_position.name in ("Leader", "Co-leader")

    return render_template("bot/consent.html", consents=consents, can_revoke_consent=can_revoke_consent)
