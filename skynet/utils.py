# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import flask
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

import redisdb


def verify_headers(request: flask.Request):
    # https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization
    
    redis = redisdb.get_redis()
    public_key = redis.get("tornium:settings:skynet:applicationpublic")
    
    verify_key = VerifyKey(bytes.fromhex(public_key))

    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = request.data.decode("utf-8")

    verify_key.verify(
        f"{timestamp}{body}".encode(),
        bytes.fromhex(signature)
    )
