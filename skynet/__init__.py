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

import logging

from flask import Blueprint, abort, jsonify, request
from nacl.exceptions import BadSignatureError
from tornium_commons.skyutils import SKYNET_INFO

import skynet.commands
import skynet.skyutils
import utils.tornium_ext

try:
    import ddtrace

    globals()["ddtrace:loaded"] = True
except (ImportError, ModuleNotFoundError):
    globals()["ddtrace:loaded"] = False

botlogger = logging.getLogger("skynet")
botlogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="skynet.log", encoding="utf-8", mode="a")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
botlogger.addHandler(handler)

mod = Blueprint("botinteractions", __name__)


def in_dev_command(interaction, *args, **kwargs):
    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Command In Development",
                    "description": "This command is not yet ready for production use.",
                    "color": SKYNET_INFO,
                }
            ]
        },
    }


_autocomplete = {"notify": skynet.commands.notify.notify_autocomplete_switchboard}
_buttons = {
    "faction:vault:cancel": skynet.commands.faction.cancel.cancel_button,
    "faction:vault:fulfill": skynet.commands.faction.fulfill.fulfill_button,
}
_commands = {
    "ping": skynet.commands.ping,
    # Faction Commands
    "assist": skynet.commands.faction.assist.assist,
    "balance": skynet.commands.faction.balance.balance,
    "cancel": skynet.commands.faction.cancel.cancel_command,
    "faction": skynet.commands.faction.faction.faction_data_switchboard,
    "fulfill": skynet.commands.faction.fulfill.fulfill_command,
    "withdraw": skynet.commands.faction.withdraw.withdraw,
    # Bot Commands
    "verify": skynet.commands.bot.verify.verify,
    "verifyall": skynet.commands.bot.verifyall.verify_all,
    # Notification Commands
    "notify": skynet.commands.notify.notify_switchboard,
    # Stat DB Commands
    "chainlist": skynet.commands.stat.chain.chain,
    "stat": skynet.commands.stat.stat.stat,
    # Stocks Commands
    "stocks": skynet.commands.stocks.stocks_switchboard,
    # User Commands
    "user": skynet.commands.user.user.user_who,
}

tornium_ext: utils.tornium_ext.TorniumExt
for tornium_ext in utils.tornium_ext.TorniumExt.__iter__():
    if tornium_ext.extension is None:
        continue

    for command in tornium_ext.extension.discord_commands:
        _commands[command["name"]] = command["function"]

    for button in tornium_ext.extension.discord_buttons:
        _buttons[button["custom_id"]] = button["function"]

    if hasattr(tornium_ext.extension, "guilds"):
        for command in tornium_ext.extension.guild_commands:
            _commands[command["name"]] = command["function"]

        for button in tornium_ext.extension.guild_buttons:
            _buttons[button["custom_id"]] = button["function"]


@mod.route("/skynet", methods=["POST"])
def skynet_interactions():
    try:  # https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization
        skynet.skyutils.verify_headers(request)
    except BadSignatureError:
        abort(401, "invalid request signature")

    if request.json["type"] == 1:
        return jsonify({"type": 1})
    elif "id" not in request.json:
        return jsonify({})

    response = skynet.skyutils.check_invoker_exists(request.json)

    if isinstance(response, dict):
        return jsonify(response)

    invoker, admin_keys = response

    if globals().get("ddtrace:loaded"):
        if request.json["type"] == 3 and request.json["data"]["component_type"] == 2:
            ddtrace.tracer.current_root_span().set_tag("command_type", "button")
            ddtrace.tracer.current_root_span().set_tag("command_id", request.json["data"]["custom_id"])
        else:
            ddtrace.tracer.current_root_span().set_tag("command_id", request.json["data"]["name"])

        if "member" in request.json:
            ddtrace.tracer.current_root_span().set_tag("user_id", request.json["member"]["user"]["id"])
        else:
            ddtrace.tracer.current_root_span().set_tag("user_id", request.json["user"]["id"])

    if request.json["type"] == 3 and request.json["data"]["component_type"] == 2:
        if request.json["data"]["custom_id"] in _buttons:
            return jsonify(
                _buttons[request.json["data"]["custom_id"]](request.json, invoker=invoker, admin_keys=admin_keys)
            )
        elif request.json["data"]["custom_id"].startswith("stakeout:flying:"):
            return jsonify(
                skynet.commands.notify.stakeouts.stakeout_flying_button(
                    request.json, invoker=invoker, admin_keys=admin_keys
                )
            )
        elif request.json["data"]["custom_id"].startswith("stakeout:hospital"):
            return jsonify(
                skynet.commands.notify.stakeouts.stakeout_hospital_button(
                    request.json, invoker=invoker, admin_keys=admin_keys
                )
            )
        elif request.json["data"]["custom_id"].startswith("notify:items:"):
            return jsonify(
                skynet.commands.notify.items.items_button_switchboard(
                    request.json, invoker=invoker, admin_keys=admin_keys
                )
            )
    elif request.json["type"] == 2:
        if request.json["data"]["name"] in _commands:
            return jsonify(
                _commands[request.json["data"]["name"]](request.json, invoker=invoker, admin_keys=admin_keys)
            )
    elif request.json["type"] == 4:
        if request.json["data"]["name"] in _autocomplete:
            return jsonify(
                _autocomplete[request.json["data"]["name"]](request.json, invoker=invoker, admin_keys=admin_keys)
            )

    return jsonify(in_dev_command(request.json))
