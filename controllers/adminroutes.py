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

import datetime
import hashlib
import inspect

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import fresh_login_required, login_user
from tornium_celery.tasks.misc import send_dm
from tornium_commons import Config
from tornium_commons.skyutils import SKYNET_INFO

from controllers.decorators import admin_required
from models.user import OverrideUser

mod = Blueprint("adminroutes", __name__)


@mod.route("/admin/load-user/<int:tid>", methods=["GET", "POST"])
@fresh_login_required
@admin_required
def load_user(tid):
    if request.method == "GET":
        return (
            render_template("admin/load_user.html"),
            200,
            {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    passphrase = request.form.get("passphrase")

    if passphrase is None:
        return (
            render_template(
                "errors/error.html",
                title="Invalid Passphrase",
                error="Your security passphrase was incorrect.",
            ),
            401,
        )
    elif Config()["admin-passphrase"] != hashlib.sha512(passphrase.encode("utf-8")).hexdigest():
        return (
            render_template(
                "errors/error.html",
                title="Invalid Passphrase",
                error="Your security passphrase was incorrect.",
            ),
            401,
        )

    try:
        user = OverrideUser(tid)
    except ValueError:
        return (
            render_template(
                "errors/error.html",
                title="Unknown User",
                error="This user is not found in the database.",
            ),
            400,
        )

    if user.key == "":
        return (
            render_template(
                "errors/error.html",
                title="Invalid User",
                error="This user is not signed in.",
            ),
            400,
        )

    if user.discord_id not in (0, "", None):
        send_dm.delay(
            user.discord_id,
            payload={
                "embeds": [
                    {
                        "title": "Security Alert",
                        "description": inspect.cleandoc(
                            """Your account is being accessed through an admin override on Tornium. This is typically done with your permission for server maintenance or bug fixing.

                        If you have any questions or concerns, please contact the admin(s) as soon as possible on the linked Discord account.

                        WARNING: If the developer is accessing your Tornium account, they will contact you ahead of time for permission through the linked Tornium account."""
                        ),
                        "color": SKYNET_INFO,
                    }
                ],
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": "tiksan [2383326] @ Discord (preferred)",
                                "url": "https://discord.com/users/695828257949352028",
                            }
                        ],
                    },
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": "tiksan [2383326] @ Torn",
                                "url": "https://www.torn.com/profiles.php?XID=2383326",
                            },
                        ],
                    },
                ],
            },
        )

    login_user(user, remember=False, duration=datetime.timedelta(minutes=10), fresh=True)

    return redirect(url_for("baseroutes.index"))
