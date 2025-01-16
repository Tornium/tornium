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

import pathlib
import typing
import uuid

import toml
from tornium_commons.models import NotificationTrigger


class TriggerConfig(typing.TypedDict):
    uuid: str
    name: str
    description: str
    owner: int


class ImplementationConfig(typing.TypedDict):
    cron: str
    resource: typing.Literal["faction", "user"]
    selections: typing.List[str]
    message_type: typing.Literal["update", "send"]
    parameters: typing.Dict[str, str]


class Config(typing.TypedDict):
    trigger: TriggerConfig
    implementation: ImplementationConfig


def load_trigger(path: pathlib.Path, official: bool = False):
    """
    Load a notification trigger by path of its directory into the database

    Parameters
    ----------
    path : pathlib.Path
        Path to the directory containing the trigger's code and others

    official : bool
        Boolean flag for whether the trigger is an official trigger
    """

    with open(f"{path}/config.toml", "r") as f:
        config_data: Config = toml.load(f)

    with open(f"{path}/code.lua", "r") as f:
        code: str = f.read()

    with open(f"{path}/message.liquid", "r") as f:
        template: str = f.read()

    # TODO: Validate data provided by files

    NotificationTrigger.insert(
        tid=uuid.UUID(config_data["trigger"]["uuid"]),
        name=config_data["trigger"]["name"],
        description=config_data["trigger"]["description"],
        owner=config_data["trigger"]["owner"],
        cron=config_data["implementation"]["cron"],
        resource=config_data["implementation"]["resource"],
        selections=config_data["implementation"]["selections"],
        code=code,
        parameters=config_data["implementation"]["parameters"],
        message_type=config_data["implementation"]["message_type"],
        message_template=template,
        official=official,
    ).on_conflict(
        conflict_target=[NotificationTrigger.tid],
        preserve=[
            NotificationTrigger.name,
            NotificationTrigger.description,
            # NOTE: Skip updating the trigger's owner for security, this can be changed in the database
            NotificationTrigger.cron,
            NotificationTrigger.resource,
            NotificationTrigger.selections,
            NotificationTrigger.code,
            NotificationTrigger.parameters,
            NotificationTrigger.message_type,
            NotificationTrigger.message_template,
            NotificationTrigger.official,
        ],
    ).execute()
