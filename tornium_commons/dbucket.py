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

from __future__ import (
    annotations,  # For return type annotation of methods returning the class
)

import time
import typing

import requests.structures

from .errors import RatelimitError
from .rds_lua_hashes import BHASH, BHASH_CALL
from .redisconnection import rds


def _strip_endpoint(endpoint) -> str:
    """
    Remove extra routing information from the endpoint for use in ratelimiting Redis keys.

    Parameters
    ----------
    endpoint : str
        Request endpoint as passed to Celery tasks

    Returns
    -------
    stripped_endpoint : str
        Endpoint used for Discord bucket hashes
    """

    without_query = endpoint.split("?")[0]
    only_resource = None

    # The Discord API utilizes top-level resources for certain bucket identifiers
    # Top-level resources included are currently limited to
    # "channels/", "guilds/", "/webhooks" (last not utilized in Tornium)
    if without_query.split("/")[0] == "guilds":
        # Per resource implementation
        # Defaults to per endpoint if not implemented below

        try:
            if without_query.split("/")[2] == "members":
                only_resource = "/".join(without_query.split("/")[:3])
        except IndexError:
            pass
    elif without_query.split("/")[0] == "channels":
        pass

    if only_resource is not None:
        return only_resource

    return without_query


def _minute_timestamp() -> int:
    """
    Generates a timestamp for the start of the minute

    Returns
    -------
    timestamp : int
        Timestamp for the start of the minute
    """

    now = int(time.time())
    return now - (now % 60)


PREFIX = "tornium:discord:ratelimit:bucket"
_se = _strip_endpoint
_m = _minute_timestamp


class DBucket:
    """
    Implementation of the Discord ratelimiter.

    This class provides support for both global and per-route rate limits via Lua scripts in the Redis server.

    References
    ----------
    https://discord.com/developers/docs/topics/rate-limits
    https://wumpy.readthedocs.io/en/latest/extending/rest-ratelimiter/
    """

    def __init__(self, bhash: typing.Optional[str]):
        """
        Initialize a new Discord ratelimiting bucket from the per-route bucket hash.

        Parameters
        ----------
        bhash : str, optional
            Discord per-route bucket hash
        """

        self._id = bhash
        self.remaining = 1  # Default value in case hash is not found
        self.limit = 1  # Default value in case hash is not found
        self.expires = _m() + 60

    @property
    def id(self):
        return self._id

    @property
    def prefix(self):
        return PREFIX

    @classmethod
    def from_endpoint(
        cls,
        method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"],
        endpoint: str,
    ) -> typing.Union[DBucket, DBucketNull]:
        """
        Initialize a new Discord ratelimiting bucket from the method and endpoint being called.

        Parameters
        ----------
        method : str
            Request method
        endpoint : str
            Request endpoint as passed to Celery tasks

        Returns
        -------
        bucket : DBucket, DBucketNull
            Discord ratelimiting bucket
        """

        # Prevents requests from being made on new endpoints that are currently being called and updated
        if rds().exists(f"{PREFIX}:{method}|{_se(endpoint)}:lock:{_m()}") == 1:
            raise RatelimitError

        client = rds()

        # bhash.lua
        bhash = client.evalsha(
            BHASH,
            1,
            f"{PREFIX}:{method}|{_se(endpoint)}",
            _m(),
            60 - (int(time.time()) % 60),
        )

        if bhash is None:
            return DBucketNull(method, endpoint)
        else:
            return cls(bhash)

    def call(self):
        """
        Indicate Discord API call being made in the Redis ratelimiting keys.

        Raises
        ------
        RatelimitError
            If the bucket has reached a ratelimit.
        """

        # bhash-call.lua
        response = rds().evalsha(
            BHASH_CALL,
            3,
            f"{self.prefix}:{self.id}:remaining:{_m()}",
            f"{self.prefix}:{self.id}:limit",
            f"tornium:discord:ratelimit:global:{_m()}",
        )

        if response is None:
            raise RatelimitError

        self.remaining = response[0]
        self.limit = response[1]
        self.expires = response[2]

    def update_bucket(
        self,
        headers: typing.Union[dict, requests.structures.CaseInsensitiveDict],
        method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"],
        endpoint: str,
    ):
        """
        Update bucket's limit and remaining Redis ratelimiting keys with the Discord response's headers.

        Parameters
        ----------
        headers : requests.structures.CaseInsensitiveDict, dict
            Response headers from Discord API call
        method : str
            Request method
        endpoint : str
            Request endpoint as passed to Celery tasks
        """

        if "X-RateLimit-Bucket" not in headers:
            return

        client = rds()
        bhash = headers["X-RateLimit-Bucket"]
        client.set(f"{PREFIX}:{method}|{_se(endpoint)}", bhash, nx=True, ex=3600)

        if "X-RateLimit-Limit" in headers:
            client.set(f"{PREFIX}:{bhash}:limit", headers["X-RateLimit-Limit"])
            self.limit = headers["X-RateLimit-Limit"]

        if "X-RateLimit-Remaining" in headers:
            client.set(
                f"{PREFIX}:{bhash}:remaining:{_m()}",
                min(int(headers["X-RateLimit-Remaining"]), self.remaining),
                ex=60,
            )
            self.remaining = min(int(headers["X-RateLimit-Remaining"]), self.remaining)

        rds().delete(f"{PREFIX}:{method}|{_se(endpoint)}:lock:{_m()}")


class DBucketNull(DBucket):
    """
    Implementation of the Discord ratelimiter for when the bucket hash for the routing is not cached.

    This class provides support for both global and per-route rate limits via Lua scripts in the Redis server.
    """

    def __init__(
        self,
        method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"],
        endpoint: str,
    ):
        """
        Initialize a new Discord ratelimiting bucket from the method and endpoint of the request.

        Parameters
        ----------
        method : str
            Request method
        endpoint : str
            Request endpoint as passed to Celery tasks
        """

        super().__init__(bhash=None)

        self.method = method
        self.endpoint = endpoint.split("?")[0]

    @property
    def id(self):
        return f"{self.method}|{self.endpoint}"

    @property
    def prefix(self):
        return PREFIX + ":temp"

    # Child function primarily exists for testing purposes
    def update_bucket(
        self,
        headers: typing.Union[dict, requests.structures.CaseInsensitiveDict],
        method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"],
        endpoint: str,
    ):
        """
        Update bucket's limit and remaining Redis ratelimiting keys with the Discord response's headers.

        Parameters
        ----------
        headers : requests.structures.CaseInsensitiveDict, dict
            Response headers from Discord API call
        method : str
            Request method
        endpoint : str
            Request endpoint as passed to Celery tasks
        """

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
                f"{PREFIX}:{bhash}:remaining:{_m()}",
                min(
                    int(headers["X-RateLimit-Remaining"]),
                    int(headers["X-RateLimit-Limit"]) - 1,
                ),
                ex=60,
            )
            self.remaining = min(
                int(headers["X-RateLimit-Remaining"]),
                int(headers["X-RateLimit-Limit"]) - 1,
            )
        elif "X-RateLimit-Remaining" in headers:
            client.set(
                f"{PREFIX}:{bhash}:remaining:{_m()}",
                min(int(headers["X-RateLimit-Remaining"]), self.remaining),
                ex=60,
            )
            self.remaining = min(int(headers["X-RateLimit-Remaining"]), self.remaining)

        rds().delete(f"{PREFIX}:{method}|{_se(endpoint)}:lock:{_m()}")
