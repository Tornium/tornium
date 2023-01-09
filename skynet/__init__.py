# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import logging

from flask import Blueprint, abort, jsonify, request
from nacl.exceptions import BadSignatureError

import skynet.commands
import skynet.skyutils

botlogger = logging.getLogger("skynet")
botlogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="skynet.log", encoding="utf-8", mode="a")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
botlogger.addHandler(handler)

mod = Blueprint("botinteractions", __name__)

_commands = {
    "ping": skynet.commands.ping,
    # Faction Commands
    "assist": skynet.commands.faction.assist.assist,
    "balance": skynet.commands.faction.balance.balance,
    "cancel": skynet.commands.faction.cancel.cancel_command,
    "fulfill": skynet.commands.faction.fulfill.fulfill_command,
    "withdraw": skynet.commands.faction.withdraw.withdraw,
    # Bot Commands
    "verify": skynet.commands.bot.verify.verify,
    "verifyall": skynet.commands.bot.verifyall.verifyall,
    # User Commands
    "who": skynet.commands.user.who.who,
    # Stat DB Commands
    "chainlist": skynet.commands.stat.chain.chain,
    "stat": skynet.commands.stat.stat.stat,
    # Stocks Commands
    "stocks": skynet.commands.stocks.stocks_switchboard,
}

_buttons = {
    "faction:vault:cancel": skynet.commands.faction.cancel.cancel_button,
    "faction:vault:fulfill": skynet.commands.faction.fulfill.fulfill_button,
}


@mod.route("/skynet", methods=["POST"])
def skynet_interactions():
    def in_dev_command(interaction):
        print(interaction)

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Command In Development",
                        "description": "This command is not yet ready for production use.",
                        "color": skynet.skyutils.SKYNET_INFO,
                    }
                ]
            },
        }

    try:  # https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization
        skynet.skyutils.verify_headers(request)
    except BadSignatureError:
        abort(401, "invalid request signature")

    if request.json["type"] == 1:
        return jsonify({"type": 1})
    elif "id" not in request.json:
        return jsonify({})

    if request.json["type"] == 3 and request.json["data"]["component_type"] == 2:
        if request.json["data"]["custom_id"] in _buttons:
            return jsonify(_buttons[request.json["data"]["custom_id"]](request.json))
    elif request.json["type"] == 2:
        if request.json["data"]["name"] in _commands:
            return jsonify(_commands[request.json["data"]["name"]](request.json))

    return jsonify(in_dev_command(request.json))
