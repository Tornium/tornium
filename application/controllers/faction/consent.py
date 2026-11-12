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
from tornium_commons.models import OAuthClientResourceConsent

from controllers.faction.decorators import aa_required, fac_required


@fresh_login_required
@fac_required
@aa_required
def consent(*args, **kwargs):
    consents: typing.List[OAuthClientResourceConsent] = [
        c
        for c in OAuthClientResourceConsent.select().where(
            (OAuthClientResourceConsent.faction == current_user.faction_id)
            & (OAuthClientResourceConsent.revoked_at.is_null(True))
        )
    ]
    can_revoke_consent = current_user.faction_position.name in ("Leader", "Co-leader")

    return render_template("faction/consent.html", consents=consents, can_revoke_consent=can_revoke_consent)
