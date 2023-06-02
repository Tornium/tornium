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

import mongoengine
import pymongo


def test_connect_mongo():
    # https://github.com/MongoEngine/mongoengine/blob/c8ef07a4189575de46c695fb27bc69a1d8b7b092/tests/test_connection.py#L47

    mongoengine.connect(
        db="Tornium",
        host="mongodb://localhost:27017",  # Assumes port 27017 for a MongoDB Docker instance
        connect=False,
    )

    connection = mongoengine.get_connection()
    assert isinstance(connection, pymongo.mongo_client.MongoClient)
