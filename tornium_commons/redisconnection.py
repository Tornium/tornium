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

import pathlib

import importlib_resources
import redis


def rds() -> redis.Redis:
    """
    Returns a redis connection from the connection pool.

    Returns
    -------
    connection : redis.Redis
    """

    return redis.Redis(host="127.0.0.1", port=6379, charset="utf-8", decode_responses=True)


def load_scripts() -> dict:
    """
    Loads Lua scripts into Redis server

    Returns
    -------
    scripts : mapping of script names to hashes
    """

    scripts = {}
    client = rds()

    client.script_flush()

    script: pathlib.Path
    for script in importlib_resources.files("rds_lua").iterdir():
        script_data = script.read_text()

        scripts[script.name[:-4]] = client.script_load(script_data)

    return scripts
