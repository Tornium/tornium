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

import json
import logging

from flask import Blueprint
import requests

from redisdb import get_redis
import tasks
import utils

mod = Blueprint("cli", __name__)


@mod.cli.command("update-commands")
def update_commands():
    with open("commands/commands.json") as commands_file:
        commands_list = json.load(commands_file)

    botlogger = logging.getLogger("skynet")
    botlogger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename="skynet.log", encoding="utf-8", mode="a")
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    botlogger.addHandler(handler)

    session = requests.Session()
    application_id = get_redis().get("tornium:settings:skynet:applicationid")
    botlogger.debug(application_id)

    commands_data = []

    for commandid in commands_list["active"]:
        with open(f"commands/{commandid}.json") as command_file:
            command_json = json.load(command_file)
            commands_data.append(command_json)

    botlogger.debug(commands_data)

    try:
        commands_data = tasks.discordput(
            f"applications/{application_id}/commands",
            commands_data,
            session=session,
        )
        botlogger.info(commands_data)
    except utils.DiscordError as e:
        botlogger.error(e)
        raise e
    except Exception as e:
        botlogger.error(e)
        raise e
