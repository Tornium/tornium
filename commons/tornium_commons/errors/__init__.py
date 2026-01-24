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

from .discord import DiscordError
from .networking import NetworkingError
from .torn import MissingKeyError, TornError

__all__ = ["DiscordError", "DiscordRatelimitError", "NetworkingError", "MissingKeyError", "TornError", "RatelimitError"]


class RatelimitError(Exception):
    """
    The request has resulted in a pre-emptive ratelimit handling or a rate-limited response.
    """

    pass


class DiscordRatelimitError(RatelimitError):
    """
    The Discord API call has resulted in a ratelimit. This ratelimit can either occur before the API call
    has been performed or after the fact.
    """

    def __init__(self, method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"], endpoint: str, source: str):
        super().__init__()

        self.method = method
        self.endpoint = endpoint
        self.source = source

    def __str__(self):
        return f"Discord API ratelimit ({self.source}): {self.method} {self.endpoint}"
