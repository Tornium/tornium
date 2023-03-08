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

import random
import time
import typing

from tornium_celery.tasks.api import tornget
from tornium_commons.errors import NetworkingError, TornError
from tornium_commons.formatters import find_list
from tornium_commons.models import FactionModel, UserModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_INFO

from skynet.skyutils import get_admin_keys, invoker_exists

def faction_data_switchboard(interaction, *args, **kwargs):
    if interaction["data"]["options"][0]["name"] == "members":
        return members_switchboard(interaction, *args, **kwargs)

    return {}


def members_switchboard(interaction, *args, **kwargs):
    payload = {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "",
                    "description": "",
                    "color": SKYNET_INFO,
                }
            ]
        }
    }

    def online():
        payload["data"]["embeds"][0]["title"] = f"Online Members of {member_data['name']}"

        for tid, member in member_data["members"].items():
            tid = int(tid)

            if member["last_action"]["status"] == "Online":
                line_payload = f"{member['name']} [{tid}] - Online - {member['last_action']['relative']}"
            elif member["last_action"]["status"] == "Idle" and int(time.time()) - member["last_action"]["timestamp"] < 600:  # Ten minutes
                line_payload = f"{member['name']} [{tid}] - Idle - {member['last_action']['relative']}"
            else:
                continue

            if(len(payload["data"]["embeds"][-1]["descriptiom"]) + 1 + len(line_payload)) > 4096:
                payload["data"]["embeds"].append(
                    {
                        "title": f"Online Members of {member_data['name']}",
                        "description": "",
                        "color": SKYNET_INFO,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload["data"]["embeds"][-1]["description"] += line_payload

        return payload

    def offline():
        return {}

    def flying():
        return {}

    def okay():
        return {}

    def hospital():
        return {}

    try:
        subcommand = interaction["data"]["options"][0]["options"][0]["name"]
        subcommand_data = interaction["data"]["options"][0]["options"][0]["options"]
    except Exception:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Interaction Format",
                        "description": "Discord has returned an invalidly formatted interaction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    user: UserModel = kwargs["invoker"]
    faction: typing.Optional[str] = find_list(subcommand_data, "name", "faction")

    if faction is None:
        faction: typing.Optional[FactionModel] = FactionModel.objects(tid=user.factionid).first()

        if faction is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Faction Not Found",
                            "description": "The faction could not be located in the database. This error is not "
                                           "currently handled.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
    elif faction.isdigit():
        faction: typing.Optional[FactionModel] = FactionModel.objects(tid=int(faction)).first()

        if faction is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Faction Not Found",
                            "description": "This faction could not be located in the database by name.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }
    else:
        faction: typing.Optional[FactionModel] = FactionModel.objects(name__iexact=faction).first()

        if faction is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Faction Not Found",
                            "description": "This faction could not be located in the database by name.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,  # Ephemeral
                },
            }

    admin_keys = kwargs["admin_keys"]
    try:
        member_data = tornget(
            "faction/?selections=",
            key=random.choice(admin_keys),
        )
    except TornError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Torn API Error",
                        "description": f'The Torn API has raised error code {e.code}: "{e.message}".',
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
    except NetworkingError as e:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "HTTP Error",
                        "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    if subcommand == "online":
        return online()
    elif subcommand == "offline":
        return {}
    elif subcommand == "flying":
        return {}
    elif subcommand == "okay":
        return {}
    elif subcommand == "hospital":
        return {}
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Command Not Found",
                        "description": "This command does not exist.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }
