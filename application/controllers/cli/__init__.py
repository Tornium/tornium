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

import importlib
import importlib.resources
import json
import logging
import os
import pathlib
import traceback
import typing

import click
from flask import Blueprint
from tornium_celery.tasks.api import discordput
from tornium_commons import Config, db, models, rds
from tornium_commons.errors import DiscordError
from tornium_commons.models import *  # noqa: F403  # Used for create_db()

mod = Blueprint("cli", __name__)

EXCLUDE_KEYS = ("function", "active", "disabled")


@mod.cli.command("create-db")
@click.option("--verbose", "-v", is_flag=True, show_default=True, default=False)
def create_db(verbose=False):
    if verbose:
        click.echo(f"Located {len(models.__all__)} models: {models}")
    else:
        click.echo(f"Located {len(models.__all__)} models...")

    with db() as _db:
        _db.create_tables([globals()[n] for n in models.__all__ if globals().get(n) is not None])

    click.echo("Tables created")


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

    application_id = Config.from_json().bot_application_id
    botlogger.debug(application_id)

    commands_data = []

    if verbose:
        click.echo("Adding default Tornium commands...")

    for commandid in commands_list["active"]:
        with open(f"commands/{commandid}.json") as command_file:
            command_json = json.load(command_file)
            commands_data.append(command_json)

    click.echo(f"{len(commands_data)} commands discovered and ready to be exported")
    botlogger.debug(commands_data)

    try:
        commands_data = discordput(
            f"applications/{application_id}/commands",
            commands_data,
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


@mod.cli.command("load-scripts")
@click.option("--verbose", "-v", is_flag=True, show_default=True, default=False)
def load_scripts(verbose=False):
    client = rds()
    client.echo("1")

    if verbose:
        click.echo("Redis connection established")

    client.script_flush()
    client.echo("Existing Redis scripts flushed")

    path = pathlib.Path.joinpath(importlib.resources.files("tornium_commons"), "rds_lua")

    click.echo(f"{sum(1 for _ in path.iterdir())} Redis scripts discovered\n")

    scripts = path.iterdir()
    script_map = {}

    script: pathlib.Path
    for script in scripts:
        script_data = script.read_text()
        try:
            script_map[script.name] = client.script_load(script_data)
        except Exception as e:
            click.echo(f'Loading of Redis script "{script.name}" has failed')

            if verbose:
                click.echo(traceback.format_exception(e))

            continue

        if verbose:
            click.echo(f'Redis script "{script.name}" has been successfully loaded')

    click.echo(f"\n{len(script_map)} Redis scripts loaded with the following SHA1 hashes...")

    for script_name, script_hash in script_map.items():
        click.echo(f"{script_name}: {script_hash}")


@mod.cli.command("load-triggers")
@click.option("--verbose", "-v", is_flag=True, show_default=True, default=False)
def load_triggers(verbose=False):
    path = pathlib.Path(os.getcwd() + "/../notifications")

    if verbose:
        click.echo(f"Walking dir {path}")

    trigger_directories: typing.List[str] = next(os.walk(path))[1]

    click.echo(f"Found {len(trigger_directories)} trigger directories")

    for trigger_directory in trigger_directories:
        if verbose:
            click.echo(f"Checking trigger directory {trigger_directory}")

        load_trigger(pathlib.Path(os.getcwd() + "/../notifications/" + trigger_directory), official=True)
