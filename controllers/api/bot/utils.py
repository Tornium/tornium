# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from controllers.api.decorators import *
from models.server import Server
import redisdb


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def get_channels(guildid, *args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        server = Server(guildid)
    except LookupError:
        return (
            {
                "code": 1001,
                "name": "UnknownGuild",
                "message": "Server failed to locate the requested guild.",
            },
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    return (
        {"channels": server.get_text_channels()},
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def get_roles(guildid, *args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        server = Server(guildid)
    except LookupError:
        return (
            {
                "code": 1001,
                "name": "UnknownGuild",
                "message": "Server failed to locate the requested guild.",
            },
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    return (
        {"roles": server.get_roles()},
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )
