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

from flask import jsonify
from tornium_celery.tasks.api import discord_request
from tornium_commons.errors import (
    DiscordError,
    MissingKeyError,
    NetworkingError,
    TornError,
)
from tornium_commons.skyutils import SKYNET_ERROR


def handle_interaction_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except NetworkingError as e:
            return jsonify(
                {
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
            )
        except TornError as e:
            return jsonify(
                {
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
            )
        except MissingKeyError:
            return jsonify(
                {
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
            )
        except DiscordError as e:
            return jsonify(
                {
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
            )

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
    @handle_interaction_errors
    def wrapper(*args, **kwargs):
        # The interaction is always the first and only arg passed into the function
        interaction: dict = args[0]
        ack_complete = threading.Event()

        def ack(interaction: dict):
            try:
                discord_request(
                    "POST",
                    f"interactions/{interaction['id']}/{interaction['token']}/callback",
                    body={"type": 5, "data": {"flags": 64}},
                )
            finally:
                ack_complete.set()

        threading.Thread(target=ack, daemon=True).start()

        slash_command_response = f(*args, **kwargs)

        ack_complete.wait()
        discord_request(
            "PATCH",
            f"webhooks/{interaction['application_id']}/{interaction['token']}/messages/@original",
            slash_command_response,
        )

        return {}

    return wrapper
