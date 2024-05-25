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
import re
import time
import typing

from peewee import DoesNotExist
from tornium_celery.tasks.api import tornget
from tornium_commons.formatters import find_list
from tornium_commons.models import Faction, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_INFO

from skynet.decorators import invoker_required
from skynet.skyutils import get_admin_keys


def faction_data_switchboard(interaction, *args, **kwargs):
    if interaction["data"]["options"][0]["name"] == "members":
        return members_switchboard(interaction, *args, **kwargs)

    return {}


@invoker_required
def members_switchboard(interaction, *args, **kwargs):
    payload = [
        {
            "title": "",
            "description": "",
            "color": SKYNET_INFO,
        }
    ]

    def online():
        payload[0]["title"] = f"Online Members of {member_data['name']}"
        indices = sorted(
            member_data["members"],
            key=lambda d: member_data["members"][d]["last_action"]["timestamp"],
            reverse=True,
        )
        member_data["members"] = {n: member_data["members"][n] for n in indices}

        for tid, member in member_data["members"].items():
            tid = int(tid)

            if member["last_action"]["status"] == "Online":
                line_payload = f"{member['name']} [{tid}] - Online - {member['last_action']['relative']}"
            elif (
                member["last_action"]["status"] == "Idle"
                and int(time.time()) - member["last_action"]["timestamp"] < 600
            ):  # Ten minutes
                line_payload = f"{member['name']} [{tid}] - Idle - {member['last_action']['relative']}"
            else:
                continue

            if (len(payload[-1]["description"]) + 1 + len(line_payload)) > 4096:
                payload.append(
                    {
                        "title": f"Online Members of {member_data['name']}",
                        "description": "",
                        "color": SKYNET_INFO,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload[-1]["description"] += line_payload

        return {
            "type": 4,
            "data": {"embeds": payload},
        }

    def offline():
        payload[0]["title"] = f"Offline Members of {member_data['name']}"
        indices = sorted(
            member_data["members"],
            key=lambda d: member_data["members"][d]["last_action"]["timestamp"],
            reverse=True,
        )
        member_data["members"] = {n: member_data["members"][n] for n in indices}

        for tid, member in member_data["members"].items():
            tid = int(tid)

            if member["last_action"]["status"] == "Offline":
                line_payload = f"{member['name']} [{tid}] - Offline - {member['last_action']['relative']}"
            elif (
                member["last_action"]["status"] == "Idle"
                and int(time.time()) - member["last_action"]["timestamp"] <= 600
            ):  # Ten minutes
                line_payload = f"{member['name']} [{tid}] - Idle - {member['last_action']['relative']}"
            else:
                continue

            if (len(payload[-1]["description"]) + 1 + len(line_payload)) > 4096:
                payload.append(
                    {
                        "title": f"Offline Members of {member_data['name']}",
                        "description": "",
                        "color": SKYNET_INFO,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload[-1]["description"] += line_payload

        return {
            "type": 4,
            "data": {"embeds": payload},
        }

    def flying():
        payload[0]["title"] = f"Abroad Members of {member_data['name']}"
        indices = sorted(
            member_data["members"],
            key=lambda d: member_data["members"][d]["last_action"]["timestamp"],
            reverse=True,
        )
        member_data["members"] = {n: member_data["members"][n] for n in indices}
        abroad_hospital_regex = re.compile("^In a .* hospital.*$")

        for tid, member in member_data["members"].items():
            tid = int(tid)

            if member["status"]["state"] in ("Traveling", "Abroad"):
                line_payload = f"{member['name']} [{tid}] - {member['status']['description']} - {member['last_action']['relative']}"
            elif member["status"]["state"] == "Hospital" and abroad_hospital_regex.match(
                member["status"]["description"]
            ):
                line_payload = f"{member['name']} [{tid}] - {member['status']['description']} - {member['last_action']['relative']}"
            else:
                continue

            if (len(payload[-1]["description"]) + 1 + len(line_payload)) > 4096:
                payload.append(
                    {
                        "title": f"Abroad Members of {member_data['name']}",
                        "description": "",
                        "color": SKYNET_INFO,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload[-1]["description"] += line_payload

        return {
            "type": 4,
            "data": {"embeds": payload},
        }

    def okay():
        payload[0]["title"] = f"Okay Members of {member_data['name']}"
        indices = sorted(
            member_data["members"],
            key=lambda d: member_data["members"][d]["last_action"]["timestamp"],
            reverse=True,
        )
        member_data["members"] = {n: member_data["members"][n] for n in indices}

        for tid, member in member_data["members"].items():
            tid = int(tid)

            if member["status"]["state"] == "Okay":
                line_payload = f"{member['name']} [{tid}] - {member['last_action']['status']} - {member['last_action']['relative']}"
            else:
                continue

            if (len(payload[-1]["description"]) + 1 + len(line_payload)) > 4096:
                payload.append(
                    {
                        "title": f"Okay Members of {member_data['name']}",
                        "description": "",
                        "color": SKYNET_INFO,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload[-1]["description"] += line_payload

        return {
            "type": 4,
            "data": {"embeds": payload},
        }

    def hospital():
        payload[0]["title"] = f"Hospitalized Members of {member_data['name']}"
        payload[0]["color"] = SKYNET_ERROR

        indices = sorted(
            member_data["members"],
            key=lambda d: member_data["members"][d]["last_action"]["timestamp"],
            reverse=True,
        )
        member_data["members"] = {n: member_data["members"][n] for n in indices}

        for tid, member in member_data["members"].items():
            tid = int(tid)

            if member["status"]["state"] != "Hospital":
                continue

            line_payload = f"{member['name']} [{tid}] - Discharged <t:{member['status']['until']}:R>"

            if (len(payload[-1]["description"]) + 1 + len(line_payload)) > 4096:
                payload.append(
                    {
                        "title": f"Hospitalized Members of {member_data['name']}",
                        "description": "",
                        "color": SKYNET_ERROR,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload[-1]["description"] += line_payload

        return {
            "type": 4,
            "data": {"embeds": payload},
        }

    def inactive():
        days: typing.Union[dict, int] = find_list(subcommand_data, "name", "days")

        if days is None:
            days = 3
        else:
            days = days["value"]

        payload[0]["title"] = f"Inactive Members of {member_data['name']}"
        indices = sorted(
            member_data["members"],
            key=lambda d: member_data["members"][d]["last_action"]["timestamp"],
        )
        member_data["members"] = {n: member_data["members"][n] for n in indices}

        for tid, member in member_data["members"].items():
            if member["status"]["state"] in ("Federal", "Fallen"):
                continue
            elif int(time.time()) - member["last_action"]["timestamp"] < days * 24 * 60 * 60:
                continue

            line_payload = f"{member['name']} [{tid}] - {member['last_action']['relative']}"

            if (len(payload[-1]["description"]) + 1 + len(line_payload)) > 4096:
                payload.append(
                    {
                        "title": f"Inactive Members of {member_data['name']}",
                        "description": "",
                        "color": SKYNET_INFO,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload[-1]["description"] += line_payload

        return {
            "type": 4,
            "data": {"embeds": payload},
        }

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
                "flags": 64,
            },
        }

    user: User = kwargs["invoker"]
    faction: typing.Union[dict, int] = find_list(subcommand_data, "name", "faction")

    if faction is None:
        if user is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "User Not Found",
                            "description": "Your user could not be found. Please sign into Tornium or verify yourself on a server using Tornium. Additionally, you may not be able to use this command as an API key is required.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        elif user.faction is None:
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
                    "flags": 64,
                },
            }

        faction = user.faction
    elif faction["value"].isdigit():
        try:
            faction: Faction = Faction.get_by_id(int(faction["value"]))
        except DoesNotExist:
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
                    "flags": 64,
                },
            }
    else:
        try:
            faction: Faction = Faction.select().where(Faction.name ** faction["value"]).get()
        except DoesNotExist:
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
                    "flags": 64,
                },
            }

    admin_keys = kwargs.get("admin_keys", get_admin_keys(interaction))

    if not isinstance(admin_keys, tuple) or len(admin_keys) == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Keys",
                        "description": "No API keys of admins could be located. Please sign into Tornium or ask a "
                        "server admin to sign in.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    member_data = tornget(
        f"faction/{faction.tid}?selections=",
        key=random.choice(admin_keys),
    )

    if subcommand == "online":
        return online()
    elif subcommand == "offline":
        return offline()
    elif subcommand == "flying":
        return flying()
    elif subcommand == "okay":
        return okay()
    elif subcommand == "hospital":
        return hospital()
    elif subcommand == "inactive":
        return inactive()
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
                "flags": 64,
            },
        }
