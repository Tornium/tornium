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

import random
from functools import wraps

import flask
from nacl.signing import VerifyKey

import redisdb
import tasks
import tasks.api
import utils
from models.faction import Faction
from models.factionmodel import FactionModel
from models.server import Server
from models.usermodel import UserModel

SKYNET_ERROR = 0xC83F49
SKYNET_GOOD = 0x32CD32
SKYNET_INFO = 0x7DF9FF


def verify_headers(request: flask.Request):
    # https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization

    redis = redisdb.get_redis()
    public_key = redis.get("tornium:settings:skynet-applicationpublic")

    verify_key = VerifyKey(bytes.fromhex(public_key))

    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = request.data.decode("utf-8")

    verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))


def get_admin_keys(interaction):
    """
    Retrieves the keys to be used for a Discord interaction

    :param interaction: Discord interaction
    """

    admin_keys = []

    if "member" in interaction:
        invoker: UserModel = UserModel.objects(discord_id=interaction["member"]["user"]["id"]).first()
    else:
        invoker: UserModel = UserModel.objects(discord_id=interaction["user"]["id"]).first()

    if invoker is not None and invoker.key not in ("", None):
        return tuple([invoker.key])

    if "guild_id" in interaction:
        server = Server(interaction["guild_id"])

        for admin in server.admins:
            admin_user: UserModel = UserModel.objects(tid=admin).first()

            if admin_user is None:
                continue
            elif admin_user.key in ("", None):
                continue

            admin_keys.append(admin_user.key)

    return tuple(admin_keys)


def get_faction_keys(interaction, faction=None):
    """
    Retrieves the AA keys to be used for a Discord interaction

    :param interaction: Discord interaction
    :param faction: Torn faction whose API keys are being retrieved
    """

    if faction is not None:
        return tuple(faction.aa_keys)

    if "member" in interaction:
        invoker: UserModel = UserModel.objects(discord_id=interaction["member"]["user"]["id"]).first()
    else:
        invoker: UserModel = UserModel.objects(discord_id=interaction["user"]["id"]).first()

    if invoker is None:
        return ()

    if invoker.key not in ("", None) and invoker.factionaa:
        return tuple([invoker.key])

    if faction is None or type(faction) not in (Faction, FactionModel):
        faction: FactionModel = FactionModel.objects(tid=invoker.factionid).first()

    if faction is None:
        return ()

    return tuple(faction.aa_keys)


def check_invoker_exists(interaction):
    if "member" in interaction:
        user: UserModel = UserModel.objects(discord_id=interaction["member"]["user"]["id"]).first()
        discord_id = interaction["member"]["user"]["id"]
    else:
        user: UserModel = UserModel.objects(discord_id=interaction["user"]["id"]).first()
        discord_id = interaction["user"]["id"]

    if user is not None and user.tid != 0:
        return user, None

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
                "flags": 64,  # Ephemeral
            },
        }

    try:
        user_data = tasks.api.tornget(
            f"user/{discord_id}?selections=profile,discord",
            random.choice(admin_keys),
        )
    except utils.TornError as e:
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
                "flags": 64,  # Ephemeral
            },
        }
    except utils.NetworkingError as e:
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
                "flags": 64,  # Ephemeral
            },
        }

    user: UserModel = UserModel.objects(tid=user_data["player_id"]).modify(
        upsert=True,
        new=True,
        set__name=user_data["name"],
        set__level=user_data["level"],
        set__last_refresh=utils.now(),
        set__discord_id=user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0,
        set__factionid=user_data["faction"]["faction_id"],
        set__status=user_data["last_action"]["status"],
        set__last_action=user_data["last_action"]["timestamp"],
    )

    if user.discord_id == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "User Requires Verification",
                        "description": "You are required to be verified officially by Torn through the "
                        "[official Torn Discord server](https://www.torn.com/discord] before being "
                        "able to utilize the banking features of this bot. Alternatively, you can "
                        "sign into [the web dashboard](https://tornium.com/faction/banking) with "
                        "your API key to send a request without verifying. If you have recently "
                        "verified yourself, please wait a minute or two before trying again.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    elif user is None:
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
                "flags": 64,  # Ephemeral
            },
        }

    return user, admin_keys


def invoker_exists(f):
    @wraps(f)
    def wrapper(interaction, *args, **kwargs):
        if "member" in interaction:
            user: UserModel = UserModel.objects(discord_id=interaction["member"]["user"]["id"]).first()
            discord_id = interaction["member"]["user"]["id"]
        else:
            user: UserModel = UserModel.objects(discord_id=interaction["user"]["id"]).first()
            discord_id = interaction["user"]["id"]

        if user is not None and user.tid != 0:
            kwargs["invoker"] = user
            kwargs["admin_keys"] = None
            return f(interaction, *args, **kwargs)

        kwargs["admin_keys"] = get_admin_keys(interaction)

        if len(kwargs["admin_keys"]) == 0:
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
                    "flags": 64,  # Ephemeral
                },
            }

        try:
            user_data = tasks.api.tornget(
                f"user/{discord_id}?selections=profile,discord",
                random.choice(kwargs["admin_keys"]),
            )
        except utils.TornError as e:
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
                    "flags": 64,  # Ephemeral
                },
            }
        except utils.NetworkingError as e:
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
                    "flags": 64,  # Ephemeral
                },
            }

        user: UserModel = UserModel.objects(tid=user_data["player_id"]).modify(
            upsert=True,
            new=True,
            set__name=user_data["name"],
            set__level=user_data["level"],
            set__last_refresh=utils.now(),
            set__discord_id=user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0,
            set__factionid=user_data["faction"]["faction_id"],
            set__status=user_data["last_action"]["status"],
            set__last_action=user_data["last_action"]["timestamp"],
        )

        if user.discord_id == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "User Requires Verification",
                            "description": "You are required to be verified officially by Torn through the "
                            "[official Torn Discord server](https://www.torn.com/discord] before being "
                            "able to utilize the banking features of this bot. Alternatively, you can "
                            "sign into [the web dashboard](https://tornium.com/faction/banking) with "
                            "your API key to send a request without verifying. If you have recently "
                            "verified yourself, please wait a minute or two before trying again.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
        elif user is None:
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
                    "flags": 64,  # Ephemeral
                },
            }

        kwargs["invoker"] = user
        return f(interaction, *args, **kwargs)

    return wrapper
