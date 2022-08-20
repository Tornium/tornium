# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json
import logging

from flask import Blueprint, request, jsonify, abort
import honeybadger
from nacl.exceptions import BadSignatureError
import requests

import redisdb
import skynet.commands
import skynet.skyutils
import tasks
import utils

botlogger = logging.getLogger("skynet")
botlogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="skynet.log", encoding="utf-8", mode="a")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
botlogger.addHandler(handler)

with open("commands/commands.json") as commands_file:
    commands_list = json.load(commands_file)

session = requests.Session()
application_id = redisdb.get_redis().get("tornium:settings:skynet:applicationid")

for commandid in commands_list["active"]:
    with open(f"commands/{commandid}.json") as command_file:
        command_data = json.load(command_file)

    try:
        command = tasks.discordpost(
            f"applications/{application_id}/commands",
            command_data,
            session=session,
            dev=True,
        )
    except utils.DiscordError as e:
        honeybadger.honeybadger.notify(
            e, context={"code": e.code, "message": e.message, "command": commandid}
        )
        continue
    except Exception as e:
        honeybadger.honeybadger.notify(e, context={"command": commandid})
        continue

    # TODO: Add permissions to certain commands (e.g. fulfill)

mod = Blueprint("botinteractions", __name__)


@mod.route("/skynet", methods=["POST"])
def skynet_interactions():
    try:  # https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization
        skynet.skyutils.verify_headers(request)
    except BadSignatureError as e:
        abort(401, "invalid request signature")

    if request.json["type"] == 1:
        return jsonify({"type": 1})
    elif "id" not in request.json:
        return jsonify({})

    if request.json["type"] == 3 and request.json["data"]["component_type"] == 2:
        if request.json["data"]["custom_id"] == "faction:vault:fulfill":
            return jsonify(skynet.commands.faction.fulfill.fulfill_button(request.json))

    # General Commands
    if request.json["data"]["name"] == "ping":
        return jsonify(skynet.commands.ping(request.json))

    # Faction Commands
    elif request.json["data"]["name"] == "assist":
        return jsonify(skynet.commands.faction.assist.assist(request.json))
    elif request.json["data"]["name"] == "balance":
        return jsonify(skynet.commands.faction.balance.balance(request.json))
    elif request.json["data"]["name"] == "withdraw":
        return jsonify(skynet.commands.faction.withdraw.withdraw(request.json))
    elif request.json["data"]["name"] == "fulfill":
        return jsonify(skynet.commands.faction.fulfill.fulfill_command(request.json))
    elif request.json["data"]["name"] == "transfer":
        return jsonify(skynet.commands.faction.transfer.transfer(request.json))

    # Bot Commands
    elif request.json["data"]["name"] == "verify":
        return {}
    elif request.json["data"]["name"] == "verifyall":
        return {}

    # User Commands
    elif request.json["data"]["name"] == "who":
        return {}

    return {}
