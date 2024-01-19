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

from peewee import DoesNotExist
from tornium_commons.models import OrganizedCrime, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD


def oc_participants_button(interaction, *args, **kwargs):
    if "guild_id" not in interaction:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Not Allowed",
                        "description": "This button can not be run in a DM.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif (
        not interaction["data"]["custom_id"].startswith("oc:participants:")
        or interaction["data"]["component_type"] != 2
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Unknown Button Press",
                        "description": "The attributes of the button pressed does not match the attributes required.",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }

    user: User = kwargs["invoker"]

    if user.faction is None:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Faction Not Located",
                        "description": "Your faction could not be located in Tornium's database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    try:
        oc: OrganizedCrime = (
            OrganizedCrime.select()
            .where(OrganizedCrime.oc_id == int(interaction["data"]["custom_id"].split(":")[-1]))
            .get()
        )
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "OC Does Not Exist",
                        "description": "The Organized Crime does not currently exist.",
                        "color": SKYNET_ERROR,
                        "footer": {"text": f"Button ID: {interaction['data']['custom_id']}"},
                    }
                ],
                "flags": 64,
            },
        }
    except ValueError:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Unknown Button Press",
                        "description": "The attributes of the button pressed does not match the attributes required.",
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        }

    participants = []

    for participant in oc.participants:
        if participant in oc.delayers:
            participants.append(f"{User.user_str(participant)}: Delayer")
        else:
            participants.append(User.user_str(participant))

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "OC Participants",
                    "description": "\n".join(participants),
                    "color": SKYNET_GOOD if len(oc.delayers) == 0 else SKYNET_ERROR,
                    "footer": {
                        "text": f"OC ID: {oc.oc_id}",
                    },
                }
            ],
            "flags": 64,
        },
    }
