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

import ipaddress

from peewee import Field


class INETField(Field):
    # See https://www.postgresql.org/docs/current/datatype-net-types.html

    field_type = "inet"

    def db_value(self, value: str | ipaddress.IPv4Address | ipaddress.IPv6Address):
        if isinstance(value, ipaddress.IPv4Address) or isinstance(value, ipaddress.IPv6Address):
            return str(value)

        return value

    def python_value(self, value):
        return ipaddress.ip_address(value)
