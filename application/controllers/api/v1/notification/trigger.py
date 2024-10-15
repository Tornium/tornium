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
import random
import subprocess
import tempfile
import typing

from flask import request

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response

# regex modified based on https://stackoverflow.com/a/57639657/12941872
# Crontab in Elixir should only accept up to minutes
# TODO: Validate this regex
# CRON_REGEX = (
#     r"(@(annually|yearly|monthly|weekly|daily|hourly))|(@every (\d+(m|h))+)|((((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5})"
# )


@session_required
@ratelimit
def create_trigger(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    trigger_name: str = data.get("name", f"trigger-{kwargs['user'].tid}-{random.randint(0, 100)}")
    trigger_description: str = data.get("description", "")
    trigger_resource: typing.Optional[str] = data.get("resource")
    code: typing.Optional[str] = data.get("code", None)

    if not isinstance(trigger_name, str):
        return make_exception_response("1000", key, details={"message": "Invalid trigger name"})
    elif len(trigger_name) == 0:
        return make_exception_response("1000", key, details={"message" "Invalid trigger name (length)"})

    # TODO: Validate the user does not have a trigger named the same thing
    # TODO: Create unique index on (user, trigger_name)

    if not isinstance(trigger_description, str):
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Invalid trigger description",
            },
        )

    if trigger_resource is None:
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "invalid trigger resource",
            },
        )
    elif trigger_resource not in ("user", "faction", "company", "factionv2"):
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "invalid trigger resource",
            },
        )

    if code is None or not isinstance(code, str) or len(code) == 0:
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Missing Lua code",
            },
        )

    with tempfile.NamedTemporaryFile() as fp:
        fp.write(code.encode("utf-8"))
        fp.seek(0)

        ret = subprocess.run(["luac", "-p", fp.name], capture_output=True, timeout=1)

        if ret.returncode == 1:
            return make_exception_response("0000", key, details={"error": ret.stderr.decode("utf-8")})

    return {}, 200, api_ratelimit_response(key)
