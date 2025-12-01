# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from flask import jsonify
from peewee import DoesNotExist
from tornium_celery.tasks.api import discordget, discordpost
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.models import Server
from tornium_commons.skyutils import SKYNET_INFO

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def get_channels(guild_id, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    return (
        jsonify({"channels": guild.get_text_channels(discord_get=discordget, include_threads=True, api=True)}),
        200,
        api_ratelimit_response(key),
    )


@session_required
@ratelimit
def test_channel(guild_id, channel_id, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild: Server = Server.select(Server.admins).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    try:
        discordpost(
            f"channels/{channel_id}/messages",
            payload={
                "content": "TEST!",
                "embeds": [
                    {
                        "title": "Test Message",
                        "description": f"This is a test message from Tornium for <#{channel_id}> in guild {guild_id}.",
                        "color": SKYNET_INFO,
                    }
                ],
            },
        )
    except DiscordError as e:
        return make_exception_response("0000", key, details={"code": e.code, "message": e.message})
    except NetworkingError as e:
        return make_exception_response("4102", key, details={"code": e.code})

    return make_exception_response("0001", key)


@session_required
@ratelimit
def get_roles(guild_id, *args, **kwargs):
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    return (
        jsonify({"roles": list(guild.get_roles(discord_get=discordget, api=True).values())}),
        200,
        api_ratelimit_response(key),
    )
