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

from functools import wraps

import mongoengine
import mongomock


def connect_mongo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        mongoengine.connect("torniumTest", host="mongomock://localhost", connect=False)
        return func(*args, **kwargs)

    return wrapper


@connect_mongo
def test_connect_mongo():
    # https://github.com/MongoEngine/mongoengine/blob/c8ef07a4189575de46c695fb27bc69a1d8b7b092/tests/test_connection.py#L47

    connection = mongoengine.get_connection()
    assert isinstance(connection, mongomock.MongoClient)
