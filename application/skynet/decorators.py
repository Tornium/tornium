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

from functools import wraps

from tornium_commons.skyutils import SKYNET_ERROR


def invoker_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs["invoker"] is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Unknown User",
                            "description": "Your Discord user could not be found in the database, so it is not know which Torn user you are which would cause issues for this slash command. To resolve this issue, please verify yourself (if this server has enabled this feature), sign into [Tornium](https://tornium.com/login), or use the `/user` command to attempt to update the database with your user.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }

        return f(*args, **kwargs)

    return wrapper
