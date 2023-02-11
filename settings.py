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

from redisdb import get_redis

try:
    file = open("settings.json")
    file.close()
except FileNotFoundError:
    data = {
        "jsonfiles": ["settings"],
        "dev": False,
        "secret": str(os.urandom(32)),
        "taskqueue": "redis",
        "username": "tornium",
        "password": "",
        "host": "",
        "skynet": {
            "applicationid": "",
            "applicationpublic": "",
            "bottoken": "",
        },
        "domain": "",
    }
    with open("settings.json", "w") as file:
        json.dump(data, file, indent=4)

with open("settings.json", "r") as file:
    data = json.load(file)

redis = get_redis()
redis.set("tornium:settings:dev", str(data.get("dev")))
redis.set("tornium:settings:secret", data.get("secret"))
redis.set("tornium:settings:taskqueue", data.get("taskqueue"))
redis.set("tornium:settings:username", data.get("username"))
redis.set("tornium:settings:password", data.get("password"))
redis.set("tornium:settings:host", data.get("host"))
redis.set(
    "tornium:settings:skynet:applicationid",
    data.get("skynet").get("applicationid") if "skynet" in data else None,
)
redis.set(
    "tornium:settings:skynet:applicationpublic",
    data.get("skynet").get("applicationpublic") if "skynet" in data else None,
)
redis.set(
    "tornium:settings:skynet:bottoken",
    data.get("skynet").get("bottoken") if "skynet" in data else None,
)
redis.set(
    "tornium:settings:domain",
    data.get("domain") if "domain" in data else None,
)
