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

from tornium_commons.skyutils import SKYNET_INFO

from skynet.commands import bot, faction, notify, stat, stocks, user


def ping(interaction, *args, **kwargs):
    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Pong",
                    "image": {"url": "https://media3.giphy.com/media/pWncxUrrNHdny/giphy.gif"},
                    "color": SKYNET_INFO,
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }
