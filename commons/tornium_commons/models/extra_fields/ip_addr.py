# https://github.com/juancarlospaco/peewee-extra-fields/
# Copyright (C) juancarlospaco
# Copyright (C) 2024 tiksan
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ipaddress

from peewee import BigIntegerField


class IPAddressField(BigIntegerField):
    """
    BigIntegerField clone but only accepts IP Address, returns ip_address.

    This works transparently with IPv4 and IPv6 Addresses.
    Inspired by:
    docs.djangoproject.com/en/1.11/ref/models/fields/#genericipaddressfield and
    https://docs.python.org/3/library/ipaddress.html#module-ipaddress
    """

    def db_value(self, value: str) -> int:
        if value and isinstance(value, (str, int)):
            try:
                ipaddress.ip_address(value)
            except Exception as error:
                raise ValueError(
                    f"""{self.__class__.__name__} IP Value is
                not a Valid IP v4 or v6 Address (valid values must be a valid
                {ipaddress.ip_address} {ipaddress.IPv4Address}): {value} --> {error}."""
                )
            else:
                return int(ipaddress.ip_address(value))  # Valid IPv4Address/IPv6Address.
        return value

    def python_value(self, value: str) -> ipaddress.IPv4Address:
        return ipaddress.ip_address(value) if value else value
