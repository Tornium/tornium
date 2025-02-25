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

import hashlib
import os

_TEMPLATE = """# This file has been autogenerated by tornium-commons (rds_lua_hasher).
# Do NOT modify this file as it may be upgraded in the next commit.
#
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

"""


def save_hashes():
    global _TEMPLATE

    for file in os.listdir("tornium_commons/rds_lua"):
        if not file.endswith(".lua"):
            continue

        with open(os.path.join("tornium_commons/rds_lua", file), "r") as f:
            _TEMPLATE += (
                f"{file[:-4].upper().replace('-', '_')} = \"{hashlib.sha1(f.read().encode('utf-8')).hexdigest()}\"\n"
            )

    with open("tornium_commons/rds_lua_hashes.py", "w") as f:
        f.write(_TEMPLATE)


if __name__ == "__main__":
    save_hashes()
