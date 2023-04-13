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

import json
import os
import pathlib
import typing

from .redisconnection import rds


class Config:
    """
    A Redis-based config caching system.
    """

    def __init__(self, file: typing.Union[pathlib.Path, str] = "settings.json"):
        """
        Initialize config with file path.

        Parameters
        ----------
        file : str, pathlib.Path
            Path to the config file
        """

        if type(file) == pathlib.Path:
            self._file = file
        else:
            self._file = pathlib.Path(file)

        self._data = {}

    def __getitem__(self, item):
        return self._data.get(item, rds().get(f"tornium:settings:{item}"))

    def __setitem__(self, key, value):
        self._data[key] = value

        if type(value) == bool:
            value = int(value)

        rds().set(key, value)

        self.save()

    def load(self):
        """
        Load data from config file into Redis cache.
        """

        if not self._file.exists():
            raise FileNotFoundError

        with open(self._file) as f:
            loaded_data: dict = json.load(f)

        for data_key, data_value in loaded_data.items():
            if type(data_value) == bool:
                data_value = int(data_value)

            rds().set(f"tornium:settings:{data_key}", data_value)

        self._data = loaded_data
        return self

    def save(self):
        """
        Save temporarily config data that can be read from `__getitem__` to the config file persistently.
        """

        if not self._file.exists():
            raise FileNotFoundError

        with open(self._file, "w") as f:
            json.dump(self._data, f, indent=4)

        return self

    def regen_secret(self):
        """
        Regenerate and save the Flask secret to the config file and Redis cache.
        """

        self.__setitem__("secret", str(os.urandom(32)))
        return self.__getitem__("secret")
