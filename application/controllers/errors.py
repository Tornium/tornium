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

from flask import Blueprint, render_template, request
from tornium_commons.errors import DiscordError, NetworkingError, TornError

from controllers.api.v1.decorators import make_exception_response

mod = Blueprint("errors", __name__)
FRONTEND_API_ROUTES = ("/api", "/api/documentation")


def is_api_route():
    return request.path.startswith("/api") and request.path not in FRONTEND_API_ROUTES


@mod.app_errorhandler(DiscordError)
def discord_error_handler(e: DiscordError):
    return render_template("errors/discord.html", code=e.code, message=e.message), 500


@mod.app_errorhandler(TornError)
def torn_error_handler(e: TornError):
    return render_template("errors/torn.html", code=e.code, message=e.message), 500


@mod.app_errorhandler(NetworkingError)
def networking_error_handler(e: NetworkingError):
    return (
        render_template("errors/networking.html", code=e.code, message=e.message),
        500,
    )


@mod.app_errorhandler(400)
def error400(e):
    return render_template("errors/400.html"), 400


@mod.app_errorhandler(401)
def error401(e):
    return render_template("errors/401.html"), 401


@mod.app_errorhandler(403)
def error403(e):
    return render_template("errors/403.html"), 403


@mod.app_errorhandler(404)
def error404(e):
    if not is_api_route():
        return render_template("errors/404.html"), 404

    return make_exception_response("4010")


@mod.app_errorhandler(405)
def error405(e):
    if not is_api_route():
        return render_template("errors/405.html"), 405

    return make_exception_response("4011")


@mod.app_errorhandler(500)
def error500(e):
    if not is_api_route():
        return render_template("errors/500.html"), 500

    return make_exception_response("5000")


@mod.app_errorhandler(501)
def error501(e):
    return render_template("errors/501.html"), 501


@mod.app_errorhandler(503)
def error503(e):
    return render_template("errors/503.html"), 503
