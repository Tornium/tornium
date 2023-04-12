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

import inspect
import math
import time
import typing

from .errors import RatelimitError
from .redisconnection import rds

PREFIX = "tornium:discord:ratelimit:bucket"


class DBucket:
    def __init__(self, bhash: typing.Optional[str]):
        self._id = bhash
        self._remaining = 1
        self.limit = 1
        self.expires = math.ceil(time.time())

    @property
    def id(self):
        return self._id

    @property
    def prefix(self):
        return PREFIX

    @property
    def remaining(self):
        if self.expires < time.time():
            self._remaining = self.limit
            self.expires = math.ceil(time.time())
            rds().set(f"{self.prefix}:{self.id}:remaining", self._remaining, ex=10)
            rds().set(f"{self.prefix}:{self.id}:expires", self.expires, ex=10)
        elif self._remaining < 0:
            self._remaining = 1
            self.expires = math.ceil(time.time())
            rds().set(f"{self.prefix}:{self.id}:remaining", self._remaining, ex=10)
            rds().set(f"{self.prefix}:{self.id}:expires", self.expires, ex=10)

        return self._remaining

    @classmethod
    def from_endpoint(cls, method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"], endpoint: str):
        if rds().exists(f"{PREFIX}:{method}|{endpoint.split('?')[0]}:lock") == 1:
            raise RatelimitError

        client = rds()

        bhash = client.eval(
            inspect.cleandoc(
                """
        local bhash = redis.call("GET", KEYS[1])

        if bhash == false then
            redis.call("SET", KEYS[1] .. ":lock", 1, "EX", 2)
            return bhash
        end

        return bhash
        """
            ),
            1,
            f"{PREFIX}:{method}|{endpoint.split('?')[0]}",
        )

        if bhash is None:
            return DBucketNull(method, endpoint)
        else:
            return cls(bhash)

    def refresh_bucket(self):
        client = rds()

        try:
            self.limit = int(client.get(f"{self.prefix}:{self.id}:limit"))
        except TypeError:
            self.limit = 1

        try:
            self._remaining = int(client.get(f"{self.prefix}:{self.id}:remaining"))
        except TypeError:
            self._remaining = self.limit
            client.set(f"{self.prefix}:{self.id}:remaining", self.limit, nx=True, ex=10)

        try:
            self.expires = int(client.get(f"{self.prefix}:{self.id}:expires"))
        except TypeError:
            self.expires = math.ceil(time.time())

    def verify(self):
        if self.remaining <= 0:
            raise RatelimitError

    def call(self):
        if time.time() >= self.expires:
            rds().set(f"{self.prefix}:{self.id}:remaining", self.remaining - 1, ex=10)
        else:
            self._remaining = int(rds().decrby(f"{self.prefix}:{self.id}:remaining", 1))

    def expire(self):
        client = rds()
        client.delete(f"{self.prefix}:{self.id}:remaining")
        client.delete(f"{self.prefix}:{self.id}:limit")
        client.delete(f"{self.prefix}:{self.id}:expires")

    def update_bucket(self, headers, method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"], endpoint: str):
        # X-RateLimit-Limit: 5
        # X-RateLimit-Remaining: 0
        # X-RateLimit-Reset: 1470173023
        # X-RateLimit-Reset-After: 1
        # X-RateLimit-Bucket: abcd1234

        if "X-RateLimit-Bucket" not in headers:
            return

        client = rds()
        bhash = headers["X-RateLimit-Bucket"]
        client.set(f"{PREFIX}:{method}|{endpoint.split('?')[0]}", bhash, nx=True, ex=3600)

        if "X-RateLimit-Limit" in headers:
            client.set(f"{PREFIX}:{bhash}:limit", headers["X-RateLimit-Limit"], ex=3600)
            self.limit = int(headers["X-RateLimit-Limit"])

        if "X-RateLimit-Reset" in headers:
            client.set(f"{PREFIX}:{bhash}:expires", math.ceil(float(headers["X-RateLimit-Reset"])), ex=60)
            self.expires = float(headers["X-RateLimit-Reset"])

        if "X-RateLimit-Remaining" in headers:
            client.set(
                f"{PREFIX}:{bhash}:remaining", min(int(headers["X-RateLimit-Remaining"]), self._remaining), ex=60
            )
            self._remaining = min(int(headers["X-RateLimit-Remaining"]), self._remaining)


class DBucketNull(DBucket):
    def __init__(self, method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"], endpoint: str):
        super().__init__(bhash=None)

        self.method = method
        self.endpoint = endpoint.split("?")[0]

    @property
    def id(self):
        return f"{self.method}|{self.endpoint}"

    @property
    def prefix(self):
        return PREFIX + ":temp"

    def refresh_bucket(self):
        super().refresh_bucket()
        self.limit = 1

    def update_bucket(self, headers, method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"], endpoint: str):
        if "X-RateLimit-Bucket" not in headers:
            return

        client = rds()
        bhash = headers["X-RateLimit-Bucket"]
        client.set(f"{PREFIX}:{method}|{endpoint.split('?')[0]}", bhash, nx=True, ex=3600)

        if "X-RateLimit-Limit" in headers:
            client.set(f"{PREFIX}:{bhash}:limit", headers["X-RateLimit-Limit"], ex=3600)
            self.limit = int(headers["X-RateLimit-Limit"])

        if "X-RateLimit-Reset" in headers:
            client.set(f"{PREFIX}:{bhash}:expires", math.ceil(float(headers["X-RateLimit-Reset"])), ex=60)
            self.expires = float(headers["X-RateLimit-Reset"])

        if "X-RateLimit-Remaining" in headers:
            client.set(f"{PREFIX}:{bhash}:remaining", min(int(headers["X-RateLimit-Remaining"]), self.limit - 1), ex=60)
            self._remaining = min(int(headers["X-RateLimit-Remaining"]), self.limit - 1)

        rds().delete(f"{PREFIX}:{method}|{endpoint.split('?')[0]}:lock")
