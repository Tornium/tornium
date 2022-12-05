# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from controllers.api.decorators import *
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.server import Server


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def get_channels(guildid, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        server = Server(guildid)
    except LookupError:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in server.admins:
        return make_exception_response("4020", key)

    return (
        {"channels": server.get_text_channels(api=True)},
        200,
        api_ratelimit_response(key),
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def get_roles(guildid, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        server = Server(guildid)
    except LookupError:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in server.admins:
        return make_exception_response("4020", key)

    return (
        {"roles": list(server.get_roles(api=True).values())},
        200,
        api_ratelimit_response(key),
    )
