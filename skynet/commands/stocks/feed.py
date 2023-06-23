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

import inspect
import typing

from tornium_commons.models import ServerModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_INFO


def feed(interaction, *args, **kwargs):
    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Location",
                        "description": "The verification command must be run in a server where verification is setup "
                        "and enabled.",
                    }
                ],
                "flags": 64,
            },
        }

    server: typing.Optional[ServerModel] = ServerModel.objects(sid=interaction["guild_id"]).first()

    if server is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Server Not Located",
                        "description": "This server could not be located in Tornium's database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif kwargs["invoker"].tid not in server.admins:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "You must be an admin in this server to run this command. Run in a DM "
                        "or in a server where you are an admin.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Stocks Feed Configuration",
                    "description": inspect.cleandoc(
                        f"""Stocks feed configuration for {server.name}...

                Feed Channel: {"Disabled" if server.stocks_channel == 0 else f"<#{server.stocks_channel}>"}

                Percent Change: {"Enabled" if server.stocks_config.get("percent_change", False) else "Disabled"}
                Market Cap Change: {"Enabled" if server.stocks_config.get("cap_change", False) else "Disabled"}
                New Day Price: {"Enabled" if server.stocks_config.get("new_day_price", False) else "Disabled"}
                Minimum Price: {"Enabled" if server.stocks_config.get("min_price", False) else "Disabled"}
                Maximum Price: {"Enabled" if server.stocks_config.get("max_price", False) else "Disabled"}
                """
                    ),
                    "footer": {"text": "To modify the feed configuration, visit the guild dashboard."},
                    "color": SKYNET_INFO,
                }
            ],
            "flags": 64,
        },
    }
