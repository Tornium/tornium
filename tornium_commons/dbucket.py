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
import time
import typing

from .errors import RatelimitError
from .redisconnection import rds

PREFIX = "tornium:discord:ratelimit:bucket"


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
        if rds().exists(f"{PREFIX}:{method}|{endpoint.split('?')[0]}:lock:{int(time.time())}") == 1:
            raise RatelimitError

        client = rds()

        # bhash.lua
        bhash = client.eval(
            inspect.cleandoc(
                """
        local bhash = redis.call("GET", KEYS[1])

        if bhash == false then
            redis.call("SET", KEYS[1] .. ":lock:" .. ARGV[1], 1, "NX", "EX", 2)
            return bhash
        end

        return bhash
        """
            ),
            1,
            f"{PREFIX}:{method}|{endpoint.split('?')[0]}",
            int(time.time()),
        )

        if bhash is None:
            return DBucketNull(method, endpoint)
        else:
            return cls(bhash)

    def call(self):
        # bhash-call.lua
        response = rds().eval(
            inspect.cleandoc(
                """
            if redis.call("SET", KEYS[3], 49, "NX", "EX", 60) == "OK" then
                return 1
            elseif tonumber(redis.call("GET", KEYS[3])) < 1 then
                return 1
            end
            
            local remaining = redis.call("GET", KEYS[1])
            local limit = false
            
            if remaining == false then
                if limit == false then
                    limit = redis.call("GET", KEYS[2])
                    
                    if limit == false then
                        limit = 1
                    else
                        limit = tonumber(limit)
                    end
                end
            
                redis.call("SET", KEYS[1], limit, "NX", "EX", 2)
            end
            
            if redis.call("EXISTS", KEYS[1]) == "0" then
                if limit == false then
                    limit = redis.call("GET", KEYS[2])
                    
                    if limit == false then
                        limit = 1
                    else
                        limit = tonumber(limit)
                    end
                end
            
                redis.call("SET", KEYS[1], limit - 1, "NX", "EX", 2)
            elseif tonumber(redis.call("GET", KEYS[1])) < 1 then
                return 0
            else
                redis.call("DECR", KEYS[1])
            end
            
            return 1
            """  # noqa: W293
            ),
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
        client.set(f"{PREFIX}:{method}|{endpoint.split('?')[0]}", bhash, nx=True, ex=3600)

        if "X-RateLimit-Limit" in headers:
            client.set(f"{PREFIX}:{bhash}:limit", headers["X-RateLimit-Limit"])

        if "X-RateLimit-Remaining" in headers:
            client.set(f"{PREFIX}:{bhash}:remaining", min(int(headers["X-RateLimit-Remaining"]), self.remaining), ex=60)
            self.remaining = min(int(headers["X-RateLimit-Remaining"]), self.remaining)

        rds().delete(f"{PREFIX}:{method}|{endpoint.split('?')[0]}:lock:{int(time.time())}")


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
        client.set(f"{PREFIX}:{method}|{endpoint.split('?')[0]}", bhash, nx=True, ex=3600)

        if "X-RateLimit-Limit" in headers:
            client.set(f"{PREFIX}:{bhash}:limit", headers["X-RateLimit-Limit"], ex=3600)
            self.limit = int(headers["X-RateLimit-Limit"])

        if "X-RateLimit-Remaining" in headers and "X-RateLimit-Limit" in headers:
            client.set(
                f"{PREFIX}:{bhash}:remaining:{int(time.time())}",
                min(int(headers["X-RateLimit-Remaining"]), headers["X-RateLimit-Limit"] - 1),
                ex=60,
            )
            self.remaining = min(int(headers["X-RateLimit-Remaining"]), headers["X-RateLimit-Limit"] - 1)
        elif "X-RateLimit_Remaining" in headers:
            client.set(
                f"{PREFIX}:{bhash}:remaining:{int(time.time())}",
                min(int(headers["X-RateLimit-Remaining"]), self.remaining),
                ex=60,
            )
            self.remaining = min(int(headers["X-RateLimit-Remaining"]), self.remaining)

        rds().delete(f"{PREFIX}:{method}|{endpoint.split('?')[0]}:lock:{int(time.time())}")
