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


class DiscordError(Exception):
    def __init__(self, code, message, url):
        super().__init__()

        self.code: int = code
        self.message: str = message
        self.url: str = url

    def __str__(self):
        return f"The Discord API has return error code {self.code}"

    def __reduce__(self):
        return self.__class__, (self.code, self.message, self.url)
