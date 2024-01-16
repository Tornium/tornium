# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import random
import typing

import flask
from nacl.signing import VerifyKey
from peewee import DoesNotExist
from tornium_celery.tasks.user import update_user
from tornium_commons import Config
from tornium_commons.errors import MissingKeyError, NetworkingError, TornError
from tornium_commons.models import Faction, Server, User
from tornium_commons.skyutils import SKYNET_ERROR

application_public = Config.from_json().bot_application_public


def verify_headers(request: flask.Request):
    # https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization
    verify_key = VerifyKey(bytes.fromhex(application_public))

    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = request.data.decode("utf-8")

    verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))


def get_admin_keys(interaction, all_keys: bool = False) -> tuple:
    """
    Retrieves the keys to be used for a Discord interaction

    :param interaction: Discord interaction
    :param all_keys: Flag for whether all applicable keys should be included
    """

    # TODO: Accept passed server model to prevent double query

    admin_keys: typing.List[str] = []

    invoker: typing.Optional[User]
    try:
        if "member" in interaction:
            invoker = User.get(User.discord_id == interaction["member"]["user"]["id"])
        else:
            invoker = User.get(User.discord_id == interaction["user"]["id"])
    except DoesNotExist:
        invoker = None

    if invoker is not None and invoker.key not in ("", None) and not all_keys:
        return tuple([invoker.key])

    if "guild_id" in interaction:
        try:
            server: Server = Server.get_by_id(interaction["guild_id"])
        except DoesNotExist:
            return tuple(admin_keys)

        for admin in server.admins:
            try:
                admin_user: User = User.select(User.key).where(User.tid == admin).get()
            except DoesNotExist:
                continue

            if admin_user.key == "" or admin_user.key is None:
                continue

            admin_keys.append(admin_user.key)

    return tuple(admin_keys)


def get_faction_keys(interaction, faction: typing.Optional[Faction] = None) -> tuple:
    """
    Retrieves the AA keys to be used for a Discord interaction

    :param interaction: Discord interaction
    :param faction: Torn faction whose API keys are being retrieved
    """

    if faction is not None:
        return tuple(faction.aa_keys)

    invoker: typing.Optional[User]
    try:
        if "member" in interaction:
            invoker = (
                User.select(User.key, User.discord_id, User.faction, User.faction_aa)
                .where(User.discord_id == interaction["member"]["user"]["id"])
                .get()
            )
        else:
            invoker = (
                User.select(User.key, User.discord_id, User.faction, User.faction_aa)
                .where(User.discord_id == interaction["user"]["id"])
                .get()
            )
    except DoesNotExist:
        return tuple()

    if invoker.key not in ("", None) and invoker.faction_aa:
        return tuple([invoker.key])

    if faction is None:
        try:
            faction = Faction.select(Faction.aa_keys).where(Faction.tid == invoker.faction_id).get()
        except DoesNotExist:
            return tuple()

    return tuple(faction.aa_keys)


def check_invoker_exists(interaction: dict):
    discord_id = None

    invoker: typing.Optional[User]
    if "member" in interaction:
        invoker = User.select().where(User.discord_id == interaction["member"]["user"]["id"]).first()
        discord_id = interaction["member"]["user"]["id"]
    else:
        invoker = User.select().where(User.discord_id == interaction["user"]["id"]).first()
        discord_id = interaction["user"]["id"]

    if invoker is None:
        return invoker, tuple()

    admin_keys = get_admin_keys(interaction)

    if len(admin_keys) == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Keys",
                        "description": "No API keys were found to be run for this command. Please sign into "
                        "Tornium or run this command in a server with signed-in admins.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif discord_id is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No Discord ID",
                        "description": "No Discord ID was found on the interaction. Please report this to the developer.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    if (
        invoker is not None and (datetime.datetime.utcnow() - invoker.last_refresh).total_seconds() > 14400
    ):  # Four hours
        try:
            update_user(key=random.choice(admin_keys), discordid=discord_id)
        except TornError as e:
            if e.code == 6:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "User Requires Verification",
                                "description": "You are required to be verified officially by Torn through the "
                                "[official Torn Discord server](https://www.torn.com/discord]. If you have recently "
                                "verified yourself, please wait a minute or two before trying again.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }

            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Torn API Error",
                            "description": f'The Torn API has raised error code {e.code}: "{e.message}".',
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        except NetworkingError as e:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "HTTP Error",
                            "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
                            "color": SKYNET_ERROR,
                        }
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
                            "description": "No API key was passed to the API call. Please try again or sign into Tornium.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        invoker = User.select().where(User.discord_id == discord_id).first()

    if invoker is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Unknown User",
                        "description": "The invoking user could not be located in the database and was not "
                        "automatically saved. Please try signing into Tornium first.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    return invoker, admin_keys
