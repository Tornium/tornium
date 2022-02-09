# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import redis

redis_client = None


def get_redis():
    global redis_client

    if not redis_client:
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            charset="utf-8",
            decode_responses=True
        )
    assert redis_client.ping()
    return redis_client
