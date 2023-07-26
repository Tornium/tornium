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

import pytest

from tornium_commons import Config


def test_config_file_default():
    config = Config()

    assert isinstance(config._file, pathlib.Path), "Invalid config file type"
    assert config._file == pathlib.Path("settings.json"), "Invalid config file path"


def test_config_file_valid_names():
    _NAMES = ["settings.json", "config.json", "asdf.json"]

    for file_name in _NAMES:
        config = Config(file=file_name)

        assert isinstance(config._file, pathlib.Path), "Invalid config file type"
        assert config._file == pathlib.Path(file_name), "Invalid config file path"


def test_config_file_invalid_names():
    _NAMES = ["settings", "settings.toml", "config.xml", "c.txt"]

    for file_name in _NAMES:
        with pytest.raises(TypeError):
            Config(file=file_name)


def test_config_load(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    _DATA = {
        "secret": "b'\\xce\\x9fL\\x8e\\xa4\\xa6\\xa39[\\xf8E\\x7f\\xc7v6d\\x1c\\x02\\xa8R`\\x9a\\x02N\\x80\\xfb\\x8aE\\xfcJ\\xf1e'",
        "username": "secure_username",
        "password": "secure_password",
        "host": "localhost:27017",
    }
    config = Config(file=path)

    with open(path, "w") as f:
        json.dump(_DATA, f, indent=4)

    config.load()

    for test_key in ["non_existent", "secret", "username", None, list]:
        assert config[test_key] == _DATA.get(test_key), f"Invalid load of config key {test_key}"


def test_config_setter(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    _DATA = {
        "secret": "b'\\xce\\x9fL\\x8e\\xa4\\xa6\\xa39[\\xf8E\\x7f\\xc7v6d\\x1c\\x02\\xa8R`\\x9a\\x02N\\x80\\xfb\\x8aE\\xfcJ\\xf1e'",
        "username": "secure_username",
        "password": "secure_password",
        "host": "localhost:27017",
    }

    open(path, "w+").close()

    config = Config(file=path)

    for key, value in _DATA.items():
        config[key] = value

    config._data = _DATA


def test_regen_secret(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    _DATA = {
        "secret": "b'\\xce\\x9fL\\x8e\\xa4\\xa6\\xa39[\\xf8E\\x7f\\xc7v6d\\x1c\\x02\\xa8R`\\x9a\\x02N\\x80\\xfb\\x8aE\\xfcJ\\xf1e'",
        "username": "secure_username",
        "password": "secure_password",
        "host": "localhost:27017",
    }
    config = Config(file=path)

    with open(path, "w") as f:
        json.dump(_DATA, f, indent=4)

    assert config["secret"] != config.regen_secret(), "Secret did not change"
