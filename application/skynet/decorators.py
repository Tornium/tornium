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

import threading
from functools import wraps

from flask import Response, jsonify
from tornium_celery.tasks.api import discord_request
from tornium_commons.errors import (
    DiscordError,
    MissingKeyError,
    NetworkingError,
    TornError,
)
from tornium_commons.skyutils import SKYNET_ERROR


def _handle_interaction_errors(f, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except NetworkingError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Networking Error",
                        "description": f"A networking error has occurred on an API call resulting in HTTP {e.code}: {e.message}",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }
    except TornError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Torn API Error",
                        "description": f"An error has occurred on a Torn API call resulting in error code {e.code}: {e.message}",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }
    except MissingKeyError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Missing API Key",
                        "description": "There wasn't an API key available for a Torn API call.",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }
    except DiscordError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Discord API Error",
                        "description": f"A Discord API error has occurred resulting in an error {e.code}: {e.message}",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }


def handle_interaction_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        response = _handle_interaction_errors(f, *args, **kwargs)

        if isinstance(response, Response):
            return response

        return jsonify(response)

    return wrapper


def invoker_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs["invoker"] is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Unknown User",
                            "description": "Your Discord user could not be found in the database, so it is not know which Torn user you are which would cause issues for this slash command. To resolve this issue, please verify yourself (if this server has enabled this feature), sign into [Tornium](https://tornium.com/login), or use the `/user` command to attempt to update the database with your user.",
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            }

        return f(*args, **kwargs)

    return wrapper


def with_deferred_response(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # The interaction is always the first and only arg passed into the function
        interaction: dict = args[0]
        ack_complete = threading.Event()

        def ack():
            try:
                discord_request(
                    "POST",
                    f"interactions/{interaction['id']}/{interaction['token']}/callback",
                    body={"type": 5, "data": {"flags": 64}},
                )
            finally:
                ack_complete.set()

        threading.Thread(target=ack, daemon=True).start()
        slash_command_response = _handle_interaction_errors(f, *args, **kwargs)

        if isinstance(slash_command_response, dict) and "data" in slash_command_response:
            # If the slash command resposne is a dict and there's a data attribute, it's a normal slash
            # command response and not one for an ACK-ed response so it would include extra keys. So we'd
            # just need to return the data in the response.
            slash_command_response = slash_command_response["data"]

        ack_complete.wait()
        discord_request(
            "PATCH",
            f"webhooks/{interaction['application_id']}/{interaction['token']}/messages/@original",
            body=slash_command_response,
        )

        return {}

    return wrapper
