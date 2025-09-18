# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import random
import re
import time
import typing

from peewee import DoesNotExist
from tornium_celery.tasks.api import discordget, discordpatch, discordpost, tornget
from tornium_commons import db
from tornium_commons.formatters import HumanTimeDelta, find_list
from tornium_commons.models import Faction, PersonalStats, Server, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO

from skynet.decorators import invoker_required
from skynet.skyutils import get_admin_keys, get_faction_keys


def faction_data_switchboard(interaction, *args, **kwargs):
    if interaction["data"]["options"][0]["name"] == "members":
        return members_switchboard(interaction, *args, **kwargs)
    elif interaction["data"]["options"][0]["name"] == "crimes":
        return crimes_switchboard(interaction, *args, **kwargs)

    return {}


@invoker_required
def crimes_switchboard(interaction, *args, **kwargs):
    def missing_members():
        interval = find_list(subcommand_data, "name", "minimum")
        interval = "1 minutes" if interval is None else interval["value"]

        if interval not in ("1 minutes", "1 hours", "4 hours", "12 hours", "1 days", "2 days"):
            return {}

        # Parameter order:
        # 0: faction ID
        # 1: interval string
        parameters = [faction.tid, interval]

        query = db.execute_sql(
            """
            SELECT
                u.tid,
                u.name,
                EXTRACT(epoch FROM (now() - oc.executed_at))
            FROM public."user" u
            LEFT JOIN (
                SELECT
                    DISTINCT ON (ocs.user_id) oc.oc_id,
                    oc.executed_at,
                    ocs.user_id,
                    oc.faction_id
                FROM
                    public.organized_crime_slot ocs
                INNER JOIN public.organized_crime oc ON
                    oc.oc_id = ocs.oc_id
                ORDER BY
                    ocs.user_id,
                    oc.ready_at DESC
            ) oc ON
                oc.user_id = u.tid
                AND oc.faction_id = u.faction_id
            WHERE
                u.faction_id = %s
                AND (oc.user_id is null OR (now() - oc.executed_at IS NOT NULL AND now() - oc.executed_at > interval %s))
            """,
            parameters,
        )

        payload = {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": f"Missing OC Members of {faction.name}",
                        "description": "",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }

        for user_id, user_name, last_oc in query:
            last_oc_delta = HumanTimeDelta()
            last_oc_delta.seconds = int(last_oc)
            payload["data"]["embeds"][0][
                "description"
            ] += f"[{user_name}](https://tcy.sh/p/{user_id}) - {str(last_oc_delta)}\n"

        if len(payload["data"]["embeds"][0]["description"]) == 0:
            payload["data"]["embeds"][0]["description"] = "All applicable members are in OCs."
            payload["data"]["embeds"][0]["color"] = SKYNET_GOOD

        return payload

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
            faction: Faction = Faction.select().where(Faction.tid == int(faction["value"])).get()
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

    if user.faction_id == faction.tid and not user.can_manage_crimes():
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "You must have the manage crimes permission to use this slash command.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction_id != faction.tid and (
        interaction.get("guild_id") is None or interaction["guild_id"] != faction.guild_id
    ):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Permission Denied",
                        "description": "For factions that are not your own faction, you must be in the faction's linked Discord server.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif user.faction_id != faction.tid:
        try:
            server = Server.select(Server.factions, Server.admins).where(Server.sid == interaction["guild_id"]).get()
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Invalid Server",
                            "description": "This server could not be found in the database.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        if faction.tid not in server.factions:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "For factions that are not your own faction, you must be in the faction's linked Discord server.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        elif user.tid not in server.admins:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "For factions that are not your own faction, you must be an admin in the faction's linked Discord server.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

    if subcommand == "missing-members":
        return missing_members()
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
            key=lambda d: member_data["members"][d]["status"]["until"],
            reverse=False,
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

    def revivable():
        if not user.faction_aa or user.faction is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "Only AA members of your faction are able to use this command.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        aa_keys = get_faction_keys(interaction, user.faction)

        if not isinstance(aa_keys, tuple) or len(aa_keys) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No API Keys",
                            "description": "No API keys of faction AA members could be located. Please sign "
                            "into Tornium or ask a faction AA member to sign in.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        member_data = tornget(
            f"faction/{faction.tid}?selections=basic,members",
            random.choice(aa_keys),
            version=2,
        )

        payload[0]["title"] = f"Revivable Members of {member_data['basic']['name']}"
        not_revivable_count = 0

        for member in member_data["members"]:
            if member["status"]["state"] in ("Federal", "Fallen"):
                continue
            elif member["revive_setting"].lower() == "no one":
                not_revivable_count += 1
                continue

            line_payload = f"{member['name']} [{member['id']}] - {member['revive_setting']}"

            if (len(payload[-1]["description"]) + 1 + len(line_payload)) > 4096:
                payload.append(
                    {
                        "title": f"Revivable Members of {member_data['basic']['name']}",
                        "description": "",
                        "color": SKYNET_INFO,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload[-1]["description"] += line_payload

        payload[0]["footer"] = {"text": f"Not Revivable: {not_revivable_count}"}

        return {
            "type": 4,
            "data": {"embeds": payload},
        }

    def revivable_other_faction():
        api_user: User
        if user.personal_stats.revives >= 1 and user.key is not None:
            api_user = user
        else:
            try:
                # TODO: Convert to subquery
                # TODO: Optimize these queries
                api_users = User.select(User.tid, User.name).where(
                    User.tid.in_(Server.select(Server.admins).where(Server.sid == interaction["guild_id"]).get().admins)
                )
                api_users = {u.tid: u for u in api_users}
                api_user = api_users[
                    random.choice(
                        PersonalStats.select(PersonalStats.user).where(
                            (PersonalStats.revives >= 1) & (PersonalStats.user.in_([u.tid for u in api_users.values()]))
                        )
                    ).user_id
                ]
            except IndexError:
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

        member_data = tornget(f"faction/{faction.tid}?selections=basic,members", api_user.key, version=2)

        payload[0]["title"] = f"Revivable Members of {member_data['basic']['name']}"
        not_revivable_count = 0

        for member in member_data["members"]:
            if member["status"]["state"] in ("Federal", "Fallen"):
                continue
            elif not member["is_revivable"]:
                not_revivable_count += 1
                continue

            line_payload = f"{member['name']} [{member['id']}]"

            if (len(payload[-1]["description"]) + 1 + len(line_payload)) > 4096:
                payload.append(
                    {
                        "title": f"Revivable Members of {member_data['basic']['name']}",
                        "description": "",
                        "color": SKYNET_INFO,
                    }
                )
            else:
                line_payload = "\n" + line_payload

            payload[-1]["description"] += line_payload

        payload[0]["footer"] = {"text": f"Not Revivable: {not_revivable_count}; Based on {api_user.tid}"}

        return {
            "type": 4,
            "data": {"embeds": payload},
        }

    def revivable_ping():
        if not user.faction_aa or user.faction is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "Only AA members of your faction are able to use this command.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        try:
            faction: Faction = Faction.select().where(Faction.tid == user.faction_id).get()
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Faction Does Not Exist",
                            "description": "Your faction does not exist in the database.",
                            "color": SKYNET_ERROR,
                        },
                    ],
                    "flags": 64,
                },
            }

        if faction.guild_id is None or faction.guild_id != int(interaction["guild_id"]):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "Your faction and this Discord server are not linked. A server admin will need to do this for this command to work.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        try:
            guild: Server = Server.select(Server.factions).where(Server.sid == faction.guild_id).get()
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Server Does Not Exist",
                            "description": "This server does not exist in the database.",
                            "color": SKYNET_ERROR,
                        },
                    ],
                    "flags": 64,
                },
            }

        if user.faction_id not in guild.factions:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "Your faction and this Discord server are not linked. A server admin will need to do this for this command to work.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        aa_keys = get_faction_keys(interaction, faction)

        if not isinstance(aa_keys, tuple) or len(aa_keys) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No API Keys",
                            "description": "No API keys of faction AA members could be located. Please sign "
                            "into Tornium or ask a faction AA member to sign in.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        member_data = tornget(
            f"faction/{faction.tid}?selections=basic,members",
            random.choice(aa_keys),
            version=2,
        )

        revivable_users = []
        revive_filter = find_list(subcommand_data, "name", "type")

        if revive_filter is None:
            revive_filter = "all"
        elif revive_filter["value"] == "all":
            revive_filter = "all"
        elif revive_filter["value"] == "everyone":
            revive_filter = "everyone"
        else:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Invalid Revive Option",
                            "description": f'"{revive_filter.get("value")}" is not a valid option.',
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        for member in member_data["members"]:
            if member["status"]["state"] in ("Federal", "Fallen"):
                continue
            elif member["revive_setting"].lower() == "no one":
                continue
            elif revive_filter == "everyone" and member["revive_setting"].lower() != "everyone":
                continue

            revivable_users.append(member["id"])

        if len(revivable_users) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No Revivable Members",
                            "description": f"No members of {member_data['name']} are revivable matching the specified filter.",
                            "color": SKYNET_GOOD,
                        }
                    ],
                    "flags": 64,
                },
            }

        revivable_users_discord_ids = [
            revivable_user.discord_id
            for revivable_user in User.select(User.discord_id).where(User.tid << revivable_users)
        ]

        return {
            "type": 4,
            "data": {
                "content": "".join([f"<@{discord_id}>" for discord_id in revivable_users_discord_ids])
                + " Turn off your revives.",
            },
        }

    def revivable_ping_other_faction():
        api_user: User
        if user.personal_stats.revives >= 1 and user.key is not None:
            api_user = user
        else:
            try:
                # TODO: Convert to subquery
                # TODO: Optimize these queries
                api_users = User.select(User.tid, User.name).where(
                    User.tid.in_(Server.select(Server.admins).where(Server.sid == interaction["guild_id"]).get().admins)
                )
                api_users = {u.tid: u for u in api_users}
                api_user = api_users[
                    random.choice(
                        PersonalStats.select(PersonalStats.user).where(
                            (PersonalStats.revives >= 1) & (PersonalStats.user.in_([u.tid for u in api_users.values()]))
                        )
                    ).user_id
                ]
            except IndexError:
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

        if faction.guild_id is None or faction.guild_id != int(interaction["guild_id"]):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "The faction and this Discord server are not linked. A server admin will need to do this for this command to work.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        try:
            guild = Server.select(Server.factions, Server.admins).where(Server.sid == faction.guild_id).get()
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Server Does Not Exist",
                            "description": "This server does not exist in the database.",
                            "color": SKYNET_ERROR,
                        },
                    ],
                    "flags": 64,
                },
            }

        if faction.tid not in guild.factions:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "The faction and this Discord server are not linked. A server admin will need to do this for this command to work.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        elif user.tid not in guild.admins:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission denied",
                            "description": "Only admins of servers linked to factions are allowed to ping for other factions.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        member_data = tornget(f"faction/{faction.tid}?selections=basic,members", api_user.key, version=2)

        revivable_users = []
        for member in member_data["members"]:
            if member["status"]["state"] in ("Federal", "Fallen"):
                continue
            elif not member["is_revivable"]:
                continue

            revivable_users.append(member["id"])

        if len(revivable_users) == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No Revivable Members",
                            "description": f"No members of {member_data['name']} are revivable matching the specified filter.",
                            "color": SKYNET_GOOD,
                        }
                    ],
                    "flags": 64,
                },
            }

        revivable_users_discord_ids = [
            revivable_user.discord_id
            for revivable_user in User.select(User.discord_id).where(User.tid << revivable_users)
        ]

        return {
            "type": 4,
            "data": {
                "content": "".join([f"<@{discord_id}>" for discord_id in revivable_users_discord_ids])
                + " Turn off your revives.",
            },
        }

    def discord():
        members = User.select(User.tid, User.name, User.discord_id).where(User.faction_id == faction.tid)

        try:
            include_unverified: bool = bool(find_list(subcommand_data, "name", "unverified")["value"])
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

        if (
            faction.guild is None
            or faction.tid not in faction.guild.factions
            or faction.guild_id != int(interaction["guild_id"])
        ):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Faction Not Linked",
                            "description": "The specified faction is not linked to this Discord server.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        # Creating a followup message is necessary due to increased Discord API latencies
        # causing sometimes frequent client-side timeouts of slash commands.
        discordpost(
            f"interactions/{interaction['id']}/{interaction['token']}/callback", {"type": 5, "data": {"flags": 64}}
        )

        server_data = discordget(
            f"guilds/{interaction['guild_id']}?with_counts=true",
        )

        listed_members = {}
        if include_unverified:
            listed_members = {
                member.tid: (member.name, None)
                for member in members.where((User.discord_id == 0) | (User.discord_id.is_null(True)))
            }

        verified_members = {
            member.discord_id: (member.tid, member.name)
            for member in members.where((User.discord_id != 0) & (User.discord_id.is_null(False)))
        }
        verified_members_ids = sorted(list(verified_members.keys()))

        faction_member_index = 0
        visited_member_count = 0
        while (
            faction_member_index < len(verified_members)
            and visited_member_count < server_data["approximate_member_count"] * 0.999
        ):
            # Keep trying to find verified members in the server while:
            # - there are still unvisited members
            # - the visited count is not approximately the approximate member count

            after = 0 if faction_member_index == 0 else verified_members_ids[faction_member_index]
            guild_members: list = discordget(f"guilds/{interaction['guild_id']}/members?limit=1000&after={after}")

            if len(guild_members) == 0:
                break

            sorted_guild_members = sorted([int(member["user"]["id"]) for member in guild_members])
            guild_member_index = 0

            while faction_member_index < len(verified_members_ids) and guild_member_index < len(sorted_guild_members):
                visited_member_count += 1

                if verified_members_ids[faction_member_index] == sorted_guild_members[guild_member_index]:
                    # The faction member is in the Discord server
                    faction_member_index += 1
                    guild_member_index += 1
                elif verified_members_ids[faction_member_index] < sorted_guild_members[guild_member_index]:
                    # The guild member has a larger Discord ID than than the faction member, so the faction
                    # member can not be in the Discord server
                    faction_member = verified_members[verified_members_ids[faction_member_index]]
                    listed_members[faction_member[0]] = (faction_member[1], verified_members_ids[faction_member_index])

                    faction_member_index += 1
                elif verified_members_ids[faction_member_index] > sorted_guild_members[guild_member_index]:
                    # The faction member has a larger Discord ID than the guild member, so we can skip this
                    # guild member
                    #
                    # If the faction member has a Discord ID larger than the last guild member listed in this
                    # list of guild members, the faction member may be in the next iteration of the API call
                    # which the loop will eventually reach
                    guild_member_index += 1

        response = {
            "embeds": [
                {
                    "title": f"Missing Members of {faction.name}",
                    "description": "",
                    "color": SKYNET_INFO,
                }
            ],
            "flags": 64,
        }

        if len(listed_members) == 0:
            response["embeds"][0][
                "description"
            ] = "There are no members of the faction missing from the Discord server."
            response["embeds"][0]["color"] = SKYNET_GOOD

            discordpatch(
                f"webhooks/{interaction['application_id']}/{interaction['token']}/messages/@original", response
            )
            return {}

        for member_id, (member_name, member_discord_id) in listed_members.items():
            if member_discord_id is None:
                response["embeds"][0]["description"] += f"{member_name} [{member_id}] - Unverified\n"
            else:
                response["embeds"][0]["description"] += f"{member_name} [{member_id}] - <@{member_discord_id}>\n"

        discordpatch(f"webhooks/{interaction['application_id']}/{interaction['token']}/messages/@original", response)
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
            faction: Faction = Faction.select().where(Faction.tid == int(faction["value"])).get()
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

    if subcommand == "revivable":
        # Skips tornget call as uses v2 of the API for this
        if faction.tid == user.faction.tid:
            return revivable()
        else:
            return revivable_other_faction()
    elif subcommand == "revivable-ping":
        # Skips tornget call as uses v2 of the API for this
        if faction.tid == user.faction.tid:
            return revivable_ping()
        else:
            return revivable_ping_other_faction()

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
    elif subcommand == "discord":
        return discord()
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
