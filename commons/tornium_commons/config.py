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
import secrets
import typing

from pydantic import AnyUrl, BaseModel, Field, PostgresDsn, RedisDsn

from .altjson import load

_T = typing.TypeVar("_T")


class Config(BaseModel):
    bot_token: str = Field()
    bot_application_id: int = Field()
    bot_application_public: str = Field()
    bot_client_secret: str = Field()

    flask_secret: str = Field()
    flask_domain: str = Field()
    flask_admin_passphrase: str = Field()

    # db_dsn would follow https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING-URIS
    db_dsn: PostgresDsn = Field()

    redis_dsn: RedisDsn = Field()

    admin_users: typing.Optional[typing.List[int]] = Field()
    admin_passphrase: typing.Optional[str] = Field()

    torn_api_uri: typing.Optional[AnyUrl] = Field(default="https://api.torn.com")

    # Internal Data
    _file: typing.Optional[pathlib.Path] = None
    _loaded = False

    @classmethod
    def from_json(
        cls: typing.Type[_T],
        file: typing.Union[pathlib.Path, str] = "settings.json",
        disable_cache=False,
    ) -> _T:
        if not disable_cache:
            from .redisconnection import rds

        file: pathlib.Path
        if not isinstance(file, pathlib.Path):
            file = pathlib.Path(file)

        if not file.exists():
            raise FileNotFoundError from None

        loaded_data: dict = load(file)

        for data_key, data_value in loaded_data.items():
            if data_key.startswith("admin_"):
                continue
            elif isinstance(data_value, bool):
                data_value = int(data_value)

            if not disable_cache:
                rds().set(f"tornium:settings:{data_key}", data_value)

        self = cls(**loaded_data)
        self._file = file
        self._loaded = True

        return self

    @classmethod
    def from_cache(cls: typing.Type[_T]) -> _T:
        from .redisconnection import rds

        _cached_data = {}

        for settings_key in Config.__fields__:
            if settings_key.startswith("_"):
                continue

            _cached_data[settings_key] = rds().get(f"tornium:settings:{settings_key}")

        self = cls(**_cached_data)
        self._file = None
        self._loaded = True

        return self

    def __getitem__(self, item: str, disable_cache: bool = False) -> typing.Any:
        if not disable_cache:
            from .redisconnection import rds

        if self._loaded:
            return getattr(self, item)

        if not disable_cache:
            cached_value = rds().get(f"tornium:settings:{item}")
        else:
            cached_value = None

        if cached_value is not None:
            return cached_value

        self.load()

        if self._loaded:
            return getattr(self, item)

        raise ValueError("Settings unable to be loaded") from None

    def __setitem__(self, key: str, value: typing.Any, disable_cache: bool = False):
        if not disable_cache:
            from .redisconnection import rds

        if self._file is None:
            raise ValueError("File is not set") from None

        setattr(self, key, value)

        if isinstance(value, bool):
            value = int(value)

        if not disable_cache:
            rds().set(key, value)

        self.save()

    def load(self, disable_cache: bool = False):
        if not disable_cache:
            from .redisconnection import rds

        if not self._file.exists():
            raise FileNotFoundError from None

        loaded_data: dict = load(self._file)

        for data_key, data_value in loaded_data.items():
            if isinstance(data_value, bool):
                data_value = int(data_value)

            if not disable_cache:
                rds().set(f"tornium:settings:{data_key}", data_value)

            setattr(self, data_key, data_value)

        self._loaded = True
        return self

    def save(self):
        if not self._file.exists():
            raise FileNotFoundError from None

        with open(self._file, "w") as f:
            f.write(self.model_dump_json(indent=4))

        return self

    def regen_secret(self, nbytes: int = 32) -> str:
        self.__setitem__("flask_secret", secrets.token_hex(nbytes))
        return self.__getitem__("flask_secret")

    def __iter__(self):
        key: str
        for key, value in super().__iter__():
            if key.startswith("_"):
                continue

            yield key, value
