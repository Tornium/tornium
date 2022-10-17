# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import flask
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from models.faction import Faction
from models.factionmodel import FactionModel
from models.server import Server
from models.usermodel import UserModel
import redisdb


def verify_headers(request: flask.Request):
    # https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization

    redis = redisdb.get_redis()
    public_key = redis.get("tornium:settings:skynet:applicationpublic")

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
        invoker: UserModel = UserModel.objects(
            discord_id=interaction["member"]["user"]["id"]
        ).first()
    else:
        invoker: UserModel = UserModel.objects(
            discord_id=interaction["user"]["id"]
        ).first()

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
        invoker: UserModel = UserModel.objects(
            discord_id=interaction["member"]["user"]["id"]
        ).first()
    else:
        invoker: UserModel = UserModel.objects(
            discord_id=interaction["user"]["id"]
        ).first()

    if invoker is None:
        return ()

    if invoker.key not in ("", None) and invoker.factionaa:
        return tuple([invoker.key])

    if faction is None or type(faction) not in (Faction, FactionModel):
        faction: FactionModel = FactionModel.objects(tid=invoker.factionid).first()

    if faction is None:
        return ()

    return tuple(faction.aa_keys)
