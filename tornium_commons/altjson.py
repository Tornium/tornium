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

if globals().get("orjson:loaded"):
    import orjson
else:
    try:
        import orjson

        globals()["orjson:loaded"] = True
    except (ValueError, ModuleNotFoundError):
        globals()["orjson:loaded"] = False


def _orjson_loaded():
    return globals().get("orjson:loaded", False)


def load(*args, **kwargs):
    with open(args[0], "rb") as f:
        if _orjson_loaded():
            return orjson.loads(f.read(), *args[1:], **kwargs)
        else:
            return json.load(f, *args[1:], **kwargs)


def loads(*args, **kwargs):
    if _orjson_loaded():
        return orjson.loads(*args, **kwargs)
    else:
        return json.loads(*args, **kwargs)


def dump(*args, native=False, **kwargs):
    # args[0]: obj
    # args[1]: fp

    with open(args[1], "w") as f:
        if _orjson_loaded():
            if native:
                return json.dump(args[0], f, **kwargs)

            return f.write(orjson.dumps(args[0]))
        else:
            return json.dump(args[0], f, **kwargs)


def dumps(*args, native=False, **kwargs):
    if _orjson_loaded():
        if native:
            return json.dumps(*args, **kwargs)

        return orjson.dumps(*args, **kwargs)
    else:
        return json.dumps(*args, **kwargs)
