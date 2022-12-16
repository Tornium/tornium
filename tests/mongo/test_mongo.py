# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

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
