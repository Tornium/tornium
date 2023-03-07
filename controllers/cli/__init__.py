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

import click
import requests
from flask import Blueprint

from tornium_celery.tasks.api import discordput
from tornium_commons import rds
from tornium_commons.errors import DiscordError

from utils.tornium_ext import TorniumExt

mod = Blueprint("cli", __name__)

EXCLUDE_KEYS = ("function", "active", "disabled")


@mod.cli.command("update-commands")
@click.option("--verbose", "-v", is_flag=True, show_default=True, default=False)
def update_commands(verbose=False):
    with open("commands/commands.json") as commands_file:
        commands_list = json.load(commands_file)

    botlogger = logging.getLogger("skynet")
    botlogger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename="skynet.log", encoding="utf-8", mode="a")
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    botlogger.addHandler(handler)

    session = requests.Session()
    application_id = rds().get("tornium:settings:skynet-applicationid")
    botlogger.debug(application_id)

    commands_data = []

    if verbose:
        click.echo("Adding default Tornium commands...")

    for commandid in commands_list["active"]:
        with open(f"commands/{commandid}.json") as command_file:
            command_json = json.load(command_file)
            commands_data.append(command_json)

    if verbose:
        click.echo("Searching for installed Tornium extensions...")

    tornium_ext: TorniumExt
    for tornium_ext in TorniumExt.__iter__():
        if verbose:
            click.echo(f"Discovered Tornium extension {tornium_ext.name}...")

        command: dict
        for command in tornium_ext.extension.discord_commands:
            commands_data.append({k: v for k, v in command.items() if k not in EXCLUDE_KEYS})

    click.echo(f"{len(commands_data)} commands discovered and ready to be exported")

    botlogger.debug(commands_data)

    try:
        commands_data = discordput(
            f"applications/{application_id}/commands",
            commands_data,
            session=session,
        )
        botlogger.info(commands_data)
    except DiscordError as e:
        botlogger.error(e)
        click.echo(f"Command export failed due to Discord API error {e.code}")
        raise e
    except Exception as e:
        botlogger.error(e)
        click.echo(f"Command export failed due to error {e}")
        raise e

    click.echo("Commands have been successfully exported")
