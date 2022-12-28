# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import redis


def test_redis_connection():
    redis_client = redis.Redis(host="localhost", port=6379, charset="utf-8", decode_responses=True)

    assert redis_client.ping()
