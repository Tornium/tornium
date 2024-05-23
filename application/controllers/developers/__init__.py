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

import flask

from controllers.developers import clients

mod = flask.Blueprint("developers_routes", __name__)


mod.add_url_rule("/developers/clients", view_func=clients.clients_list, methods=["GET"])
mod.add_url_rule("/developers/clients", view_func=clients.create_client, methods=["POST"])
mod.add_url_rule(
    "/developers/clients/<client_id>",
    view_func=clients.client_dashboard,
    methods=["GET"],
)
