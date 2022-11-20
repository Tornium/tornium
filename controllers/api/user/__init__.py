# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from controllers.api.decorators import *


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:user"})
def get_user(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    return (
        jsonify(
            {
                "tid": kwargs["user"].tid,
                "name": kwargs["user"].name,
                "username": f'{kwargs["user"].name} [{kwargs["user"].tid}]',
                "last_refresh": kwargs["user"].last_refresh,
                "battlescore": kwargs["user"].battlescore,
                "battlescore_update": kwargs["user"].battlescore_update,
                "discord_id": kwargs["user"].discord_id,
                "factiontid": kwargs["user"].factionid,
                "aa": kwargs["user"].factionaa,
                "status": kwargs["user"].status,
                "last_action": kwargs["user"].last_action,
                "pro": kwargs["user"].pro,
                "pro_expiration": kwargs["user"].pro_expiration,
            }
        ),
        200,
        {
            "X-RateLimit-Limit": 250,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )
