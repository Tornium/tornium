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

import time
import typing

from .errors import RatelimitError
from .redisconnection import rds


def _strip_endpoint(endpoint):
    without_query = endpoint.split("?")[0]

    # The Discord API utilizes top-level resources for certain bucket identifiers
    # Top-level resources included are currently limited to
    # "channel/", "guild/", "/webhooks" (last not utilized in Tornium)
    if without_query.split("/")[0] in ("channel", "guild"):
        only_resource = "/".join(without_query.split("/")[:2])
        return only_resource
    else:
        return without_query


PREFIX = "tornium:discord:ratelimit:bucket"
_se = _strip_endpoint


class DBucket:
    def __init__(self, bhash: typing.Optional[str]):
        self._id = bhash
        self.remaining = 1
        self.expires = int(time.time())

    @property
    def id(self):
        return self._id

    @property
    def prefix(self):
        return PREFIX

    @classmethod
    def from_endpoint(cls, method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"], endpoint: str):
        if rds().exists(f"{PREFIX}:{method}|{_se(endpoint)}:lock:{int(time.time())}") == 1:
            raise RatelimitError

        client = rds()

        # bhash.lua
        bhash = client.evalsha(
            "6bbd164e23cda5b6366755bc514ecb976d62e93f",
            1,
            f"{PREFIX}:{method}|{_se(endpoint)}",
            int(time.time()),
        )

        if bhash is None:
            return DBucketNull(method, endpoint)
        else:
            return cls(bhash)

    def call(self):
        # bhash-call.lua
        response = rds().evalsha(
            "470c9c6ac61fc06cd6a2f10dcc61292476cf20b8",
            3,
            f"{self.prefix}:{self.id}:remaining:{int(time.time())}",
            f"{self.prefix}:{self.id}:limit",
            f"tornium:discord:ratelimit:global:{int(time.time())}",
        )

        if response == 0:
            raise RatelimitError

    def expire(self):
        client = rds()
        client.delete(f"{self.prefix}:{self.id}:remaining:{int(time.time())}")
        client.delete(f"{self.prefix}:{self.id}:limit")

    def update_bucket(self, headers, method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"], endpoint: str):
        if "X-RateLimit-Bucket" not in headers:
            return

        client = rds()
        bhash = headers["X-RateLimit-Bucket"]
        client.set(f"{PREFIX}:{method}|{_se(endpoint)}", bhash, nx=True, ex=3600)

        if "X-RateLimit-Limit" in headers:
            client.set(f"{PREFIX}:{bhash}:limit", headers["X-RateLimit-Limit"])

        if "X-RateLimit-Remaining" in headers:
            client.set(f"{PREFIX}:{bhash}:remaining", min(int(headers["X-RateLimit-Remaining"]), self.remaining), ex=60)
            self.remaining = min(int(headers["X-RateLimit-Remaining"]), self.remaining)

        rds().delete(f"{PREFIX}:{method}|{_se(endpoint)}:lock:{int(time.time())}")


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

    def update_bucket(self, headers, method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"], endpoint: str):
        if "X-RateLimit-Bucket" not in headers:
            return

        client = rds()
        bhash = headers["X-RateLimit-Bucket"]
        client.set(f"{PREFIX}:{method}|{_se(endpoint)}", bhash, nx=True, ex=3600)

        if "X-RateLimit-Limit" in headers:
            client.set(f"{PREFIX}:{bhash}:limit", headers["X-RateLimit-Limit"], ex=3600)
            self.limit = int(headers["X-RateLimit-Limit"])

        if "X-RateLimit-Remaining" in headers and "X-RateLimit-Limit" in headers:
            client.set(
                f"{PREFIX}:{bhash}:remaining:{int(time.time())}",
                min(int(headers["X-RateLimit-Remaining"]), int(headers["X-RateLimit-Limit"]) - 1),
                ex=60,
            )
            self.remaining = min(int(headers["X-RateLimit-Remaining"]), int(headers["X-RateLimit-Limit"]) - 1)
        elif "X-RateLimit_Remaining" in headers:
            client.set(
                f"{PREFIX}:{bhash}:remaining:{int(time.time())}",
                min(int(headers["X-RateLimit-Remaining"]), self.remaining),
                ex=60,
            )
            self.remaining = min(int(headers["X-RateLimit-Remaining"]), self.remaining)

        rds().delete(f"{PREFIX}:{method}|{_se(endpoint)}:lock:{int(time.time())}")
