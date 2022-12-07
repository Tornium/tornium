# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from controllers.api.decorators import *
from controllers.api.utils import api_ratelimit_response


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "read:user"})
def get_user(*args, **kwargs):
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
            }
        ),
        200,
        api_ratelimit_response(key),
    )
