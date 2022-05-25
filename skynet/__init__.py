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
import skynet.utils
import tasks
import utils

botlogger = logging.getLogger("skynet")
botlogger.setLevel(logging.debug)
handler = logging.FileHandler(
    filename="skynet.log",
    encoding="utf-8",
    mode="a"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
botlogger.addHandler(handler)

with open("commands/commands.json") as commands_file:
    commands_list = json.load(commands_file)

session = requests.Session()
application_id = redisdb.get_redis().get("tornium:settings:skynet:applicationid")

commands = {}

for commandid in commands_list["active"]:
    with open(f"commands/{commandid}.json") as command_file:
        command = json.load(command_file)
    
    try:
        command = tasks.discordpost(
            f"applications/{application_id}/commands",
            command,
            session=session,
            dev=True
        )
    except utils.DiscordError as e:
        honeybadger.notify(
            e,
            context={
                "code": e.code,
                "message": e.message,
                "command": commandid
            }
        )
        continue
    except Exception as e:
        honeybadger.notify(
            e,
            context={
                "command": commandid
            }
        )
        continue

    commands[command["id"]] = command
    
    # TODO: Add permissions to certain commands (e.g. fulfill)

mod = Blueprint("botinteractions", __name__)


@mod.route("/skynet", methods=["POST"])
def skynet():
    try:  # https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization
        skynet.utils.verify_header(request)
    except BadSignatureError as e:
        abort(401, 'invalid request signature')

    if request.json["type"] == 1:
        return jsonify({
            "type": 1
        })
    elif "id" not in request.json:
        return jsonify({})
    
    command_name = commands[request.json["id"]]["name"]

    if command_name == "ping":
        return jsonify(skynet.commands.ping(request.json))
