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

import datetime
import time
import typing

from peewee import DoesNotExist
from tornium_celery.tasks.api import discordpost
from tornium_commons import rds
from tornium_commons.formatters import discord_escaper, find_list
from tornium_commons.models import Faction, Notification, Server, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO

from skynet.decorators import invoker_required

_STYPE_NID_MAP = {
    "user": 1,
    "faction": 2,
}
_REVERSE_STYPE_NID_MAP = {
    1: "user",
    2: "faction",
}
_SCATS = {
    "user": {
        "online": 0,
        "offline": 1,
        "flying": 2,
        "okay": 3,
        "hospital": 4,
    },
    "faction": {
        "members": 0,
        "member status": 1,
        "member online": 2,
        "member offline": 3,
        "member flying": 4,
        "naps": 5,
    },
}
_REVERSE_SCATS = {
    "user": {
        0: "online",
        1: "offline",
        2: "flying",
        3: "okay",
        4: "hospital",
    },
    "faction": {
        0: "members",
        1: "member status",
        2: "member online",
        3: "member offline",
        4: "member flying",
        5: "naps",
    },
}


@invoker_required
def stakeouts(interaction, *args, **kwargs):
    def category():
        if notifications.count() > 1:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Too Many Stakeouts",
                            "description": f"{notifications.count()} stakeouts were located with the passed "
                            f"configuration.",
                            "color": SKYNET_INFO,
                        }
                    ],
                    "flags": 64,
                },
            }

        try:
            passed_scat = find_list(subcommand_data, "name", "category")["value"].lower()
        except (KeyError, ValueError):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Missing Parameter",
                            "description": "The interaction is missing the category paramter.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        try:
            notification: Notification = notifications.get()
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Stakeout Not Found",
                            "description": "No matching stakeout was located in the database.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        if notification.n_type == 1:
            scat_id = _SCATS["user"][passed_scat]
        elif notification.n_type == 2:
            scat_id = _SCATS["faction"][passed_scat]
        else:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Stakeout Type",
                            "description": "The stakeout type was not identified.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        if scat_id in notification.options["value"]:
            values = list(notification.options["value"])
            values.remove(scat_id)
            notification.options["value"] = values
            notification.save()

            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Stakeout Category Removed",
                            "description": f"The {passed_scat} stakeout category has been removed from the stakeout.",
                            "color": SKYNET_GOOD,
                            "footer": {
                                "text": f"DB ID: {notification.get_id()}",
                            },
                        }
                    ]
                },
            }
        else:
            values = list(notification.options["value"])
            values.append(scat_id)
            notification.options["value"] = values
            notification.save()

            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Stakeout Category Added",
                            "description": f"The {passed_scat} stakeout category has been added to the stakeout.",
                            "color": SKYNET_GOOD,
                            "footer": {
                                "text": f"DB ID: {notification.get_id()}",
                            },
                        }
                    ]
                },
            }

    def delete():
        try:
            notification: Notification = notifications.get()
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Stakeout Not Found",
                            "description": "No matching stakeout was located in the database.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        notification.delete_instance()

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Notification Deleted",
                        "description": "The first specified notification has been deleted.",
                        "color": SKYNET_GOOD,
                        "footer": {
                            "text": f"DB ID: {notification.get_id()}",
                        },
                    }
                ]
            },
        }

    def info():
        embeds = []

        notification: Notification
        for notification in notifications:
            notification_object: typing.Optional[typing.Union[User, Faction]]
            if notification.n_type == 1:
                notification_object = User.select().where(User.tid == notification.target).first()
                title = "User Stakeout"
            else:
                notification_object = Faction.select().where(Faction.tid == notification.target).first()
                title = "Faction Stakeout"

            if len(notification.options["value"]) == 0:
                categories = "None"
            else:
                categories = ", ".join(
                    [
                        _REVERSE_SCATS[_REVERSE_STYPE_NID_MAP[notification.n_type]][value]
                        for value in notification.options["value"]
                    ]
                )

            embeds.append(
                {
                    "title": f"{title}",
                    "color": SKYNET_INFO,
                    "fields": [
                        {
                            "name": "Target",
                            "value": f"{notification_object.name if notification_object is not None else 'N/A'} [{notification.target}]",
                        },
                        {
                            "name": "Staked-out Categories",
                            "value": categories,
                            "inline": True,
                        },
                        {
                            "name": "Enabled",
                            "value": notification.enabled,
                            "inline": True,
                        },
                        {  # Newline in fields
                            "name": "\u200B",
                            "value": "\u200B",
                            "inline": True,
                        },
                        {
                            "name": "Private",
                            "value": notification.recipient_guild == 0,
                            "inline": True,
                        },
                        {
                            "name": "Target Channel",
                            "value": (
                                f"<#{notification.recipient}>"
                                if notification.recipient_guild != 0
                                else "Direct Message"
                            ),
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": f"DB ID: {notification.get_id()}",
                    },
                }
            )

        return {
            "type": 4,
            "data": {
                "embeds": embeds,
            },
        }

    def initialize():
        channel = find_list(subcommand_data, "name", "channel")

        if channel is None:
            channel = None
            private = True
        else:
            channel = channel["value"]
            private = False

        if private and user.discord_id == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Verification Required",
                            "description": "Verification is required for private notifications.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        elif not private and ("member" not in interaction or "guild_id" not in interaction):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Command Input",
                            "description": "The command must be run in a server for a channel to be passed.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        if not private:
            try:
                guild: Server = Server.select().where(Server.sid == interaction["guild_id"]).get()
            except DoesNotExist:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Server Not Located",
                                "description": "This server could not be located in Tornium's database.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }

            if user.tid not in guild.admins:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Permission Denied",
                                "description": "You must be a server admin to run this command in this server. Please "
                                "try in another server where you admin or in a DM.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }

        if private:
            if (
                Notification.select()
                .where(
                    (Notification.invoker == user.tid)
                    & (Notification.recipient == user.discord_id)
                    & (Notification.recipient_guild == 0)
                    & (Notification.target == tid)
                    & (Notification.n_type == _STYPE_NID_MAP[stype])
                )
                .exists()
            ):
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Notification Exists",
                                "description": "This notification already exists.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }
        else:
            if (
                Notification.select()
                .where(
                    (Notification.recipient_guild == int(interaction["guild_id"]))
                    & (Notification.target == tid)
                    & (Notification.n_type == _STYPE_NID_MAP[stype])
                )
                .exists()
            ):
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Notification Exists",
                                "description": "This notification already exists.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }

        notification = Notification(
            invoker=user.tid,
            time_created=datetime.datetime.utcnow(),
            recipient=user.discord_id if private else channel,
            recipient_guild=int(interaction["guild_id"]) if not private else 0,
            n_type=_STYPE_NID_MAP[stype],
            target=tid,
            persistent=True,
            enabled=False,
            options={
                "value": [],
            },
        ).save()

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Stakeout Created",
                        "description": "A stakeout notification has been created with the following configuration.",
                        "color": SKYNET_GOOD,
                        "fields": [
                            {
                                "name": "Torn ID",
                                "value": tid,
                                "inline": True,
                            },
                            {
                                "name": "Stakeout Type",
                                "value": stype,
                                "inline": True,
                            },
                            {
                                "name": "Private",
                                "value": private,
                                "inline": True,
                            },
                            {
                                "name": "Target Channel",
                                "value": f"<#{channel}>" if private else "Direct Message",
                                "inline": True,
                            },
                        ],
                        "footer": {
                            "text": f"DB ID: {notification}",
                        },
                    }
                ]
            },
        }

    def list_notfs():
        payload = {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "List of Stakeouts",
                        "description": f"{notifications.count()} stakeouts located...\n",
                        "color": SKYNET_INFO,
                    }
                ]
            },
        }

        notification: Notification
        for notification in notifications:
            if notification.recipient_guild == 0:
                payload["data"]["embeds"][0][
                    "description"
                ] += f"\n{_REVERSE_STYPE_NID_MAP[notification.n_type]} stakeout on {notification.target} - DM"
            else:
                payload["data"]["embeds"][0][
                    "description"
                ] += f"\n{_REVERSE_STYPE_NID_MAP[notification.n_type]} stakeout on {notification.target} - <#{notification.recipient}>"

        return payload

    def toggle(mode: str):
        if notifications.count() > 1:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Too Many Stakeouts",
                            "description": f"{notifications.count()} stakeouts were located with the passed "
                            f"configuration.",
                            "color": SKYNET_INFO,
                        }
                    ],
                    "flags": 64,
                },
            }

        try:
            notification: Notification = notifications.get()
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No Matching Stakeouts",
                            "description": "No stakeouts were found that matched the searched parameters.",
                            "color": SKYNET_INFO,
                        }
                    ],
                    "flags": 64,
                },
            }

        if mode == "enable":
            mode_bool = True
        else:
            mode_bool = False

            if notification.n_type == 2 and 0 in notification.options["value"]:
                rds().delete(f"tornium:stakeout-data:faction:{notification.target}:members")

        if notification.options.get("enabled") == mode_bool:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Stakeout Issue",
                            "description": f"Stakeout is already {mode}d.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        notification.enabled = mode_bool
        notification.save()

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": f"Stakeout {mode.capitalize()}d",
                        "description": f"The stakeout on ID {notification.target} has been {mode}d. For more "
                        f"information, check out the `/notify stakeout info` command.",
                        "color": SKYNET_GOOD,
                    }
                ]
            },
        }

    # End of stakeout function

    user: User = kwargs["invoker"]

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

    tid = find_list(subcommand_data, "name", "tid")
    stype = find_list(subcommand_data, "name", "type")

    if tid is not None:
        tid = tid["value"]

    if stype is not None:
        stype = stype["value"]

    if subcommand != "initialize":
        if "guild_id" in interaction:
            try:
                guild: Server = Server.select().where(Server.sid == interaction["guild_id"]).first()
            except DoesNotExist:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Server Not Located",
                                "description": "This server could not be located in Tornium's database.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }

            if user.tid not in guild.admins:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Permission Denied",
                                "description": "You must be an admin in this server to run this command. Run in a DM "
                                "or in a server where you are an admin.",
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "flags": 64,
                    },
                }

        if tid is None:
            notifications = Notification.select()
        else:
            notifications = Notification.select().where(Notification.target == tid)

        if stype is not None:
            notifications = notifications.where(Notification.n_type == _STYPE_NID_MAP[stype])
        else:
            notifications = notifications.where(Notification.n_type.in_(list(_STYPE_NID_MAP.values())))

        if "guild_id" in interaction:
            notifications = notifications.where(
                (Notification.recipient_guild == int(interaction["guild_id"]))
                | ((Notification.recipient_guild == 0) & (Notification.invoker == user.tid))
            )
        else:
            notifications = notifications.where(
                (Notification.recipient_guild == 0) & (Notification.invoker == user.tid)
            )

        if notifications.count() == 0:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "No Stakeout Found",
                            "description": "No stakeouts could be located with the passed Torn ID and stakeout type.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flag": 64,
                },
            }

    if subcommand == "category":
        return category()
    elif subcommand == "delete":
        return delete()
    elif subcommand in ("enable", "disable"):
        return toggle(subcommand)
    elif subcommand == "info":
        return info()
    elif subcommand == "initialize":
        return initialize()
    elif subcommand == "list":
        return list_notfs()
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
def stakeout_autocomplete(interaction, *args, **kwargs):
    def category_autocomplete():
        for option in subcommand_data:
            if option.get("focused"):
                return {
                    "type": 8,
                    "data": {
                        "choices": [
                            {"value": category, "name": category}
                            for category in _SCATS[_REVERSE_STYPE_NID_MAP[notification.n_type]].keys()
                            if category.startswith(option["value"])
                        ]
                    },
                }

        return {
            "type": 8,
            "data": {
                "choices": [],
            },
        }

    user: User = kwargs["invoker"]

    try:
        subcommand = interaction["data"]["options"][0]["options"][0]["name"]
        subcommand_data = interaction["data"]["options"][0]["options"][0]["options"]
    except Exception:
        return {
            "type": 8,
            "data": {
                "choices": [],
            },
        }

    tid = find_list(subcommand_data, "name", "tid")
    stype = find_list(subcommand_data, "name", "type")

    if tid is not None:
        tid = tid["value"]

    if stype is not None:
        stype = stype["value"]

    notifications = Notification.select().where(Notification.target == tid)

    if stype is not None:
        notifications = notifications.where(Notification.n_type == _STYPE_NID_MAP[stype])

    if "guild_id" in interaction:
        notifications = notifications.where(
            (Notification.recipient_guild == int(interaction["guild_id"]))
            | ((Notification.recipient_guild == 0) & (Notification.invoker == user.tid))
        )
    else:
        notifications = notifications.where((Notification.recipient_guild == 0) & (Notification.invoker == user.tid))

    if notifications.count() != 1:
        return {
            "type": 8,
            "data": {
                "choices": [],
            },
        }

    notification: Notification = notifications.get()

    if subcommand == "category":
        return category_autocomplete()
    else:
        return {
            "type": 8,
            "data": {
                "choices": [],
            },
        }


def stakeout_flying_button(interaction, *args, **kwargs):
    button_data = interaction["data"]["custom_id"].split(":")
    tid = int(button_data[2])
    flying_type = button_data[3]
    arrival_ts = int(button_data[4])

    if arrival_ts - 60 < int(time.time()):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Arrival Too Soon",
                        "description": "This user has already landed or is close to landing.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    user: typing.Optional[User] = User.select().where(User.tid == tid).first()

    _flying_type_str = {
        0: "Standard",
        1: "Airstrip",
        2: "Wind Lines Travel",
        3: "Business Class Ticket",
    }

    dm_channel = discordpost(
        "users/@me/channels",
        payload={
            "recipient_id": (
                interaction["member"]["user"]["id"] if "guild_id" in interaction else interaction["user"]["id"]
            ),
        },
    )

    payload = {
        "embeds": [
            {
                "title": f"{'Unknown' if user is None else discord_escaper(user.name)} is Landing",
                "description": (
                    f"{'Unknown' if user is None else discord_escaper(user.name)} [{tid}] is landing within the next minute if they're "
                    f"flying with {_flying_type_str[int(flying_type)]}."
                ),
                "color": SKYNET_INFO,
            },
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Profile",
                        "url": f"https://www.torn.com/profiles.php?XID={tid}",
                    },
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Attack Link",
                        "url": f"https://www.torn.com/loader.php?sid=attack&user2ID={tid}",
                    },
                ],
            }
        ],
    }

    task = discordpost.apply_async(
        kwargs={
            "endpoint": f"channels/{dm_channel['id']}/messages",
            "payload": payload,
            "bucket": f"channels/{dm_channel['id']}",
        },
        eta=datetime.datetime.utcfromtimestamp(arrival_ts),
    )
    task.forget()

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Notification Queued",
                    "description": f"The selected notification has been enqueued for <t:{arrival_ts}:R>.",
                    "color": SKYNET_GOOD,
                    "footer": {
                        "text": f"Task ID: {task.id}",
                    },
                },
            ],
            "flags": 64,
        },
    }


def stakeout_hospital_button(interaction, *args, **kwargs):
    button_data = interaction["data"]["custom_id"].split(":")
    tid = int(button_data[2])
    until_ts = int(button_data[3])

    if until_ts - 60 < int(time.time()):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Hospital End Too Soon",
                        "description": "This user has already left hospital or is close to leaving the hospital.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    user = User.select().where(User.tid == tid).first()

    dm_channel = discordpost(
        "users/@me/channels",
        payload={
            "recipient_id": (
                interaction["member"]["user"]["id"] if "guild_id" in interaction else interaction["user"]["id"]
            )
        },
    )

    payload = {
        "embeds": [
            {
                "title": f"{'Unknown' if user is None else discord_escaper(user.name)} is Leaving Hospital",
                "description": f"{'Unknown' if user is None else discord_escaper(user.name)} is leaving the hospital within the "
                f"next minute or so.",
                "color": SKYNET_INFO,
            }
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Profile",
                        "url": f"https://www.torn.com/profiles.php?XID={tid}",
                    },
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Attack Link",
                        "url": f"https://www.torn.com/loader.php?sid=attack&user2ID={tid}",
                    },
                ],
            }
        ],
    }

    task = discordpost.apply_async(
        kwargs={
            "endpoint": f"channels/{dm_channel['id']}/messages",
            "payload": payload,
            "bucket": f"channels/{dm_channel['id']}",
        },
        eta=datetime.datetime.utcfromtimestamp(until_ts),
    )

    redis_client = rds()
    redis_client.sadd(f"tornium:stakeout-notif:user:{tid}:hospital", task.id)
    redis_client.expireat(
        f"tornium:stakeout-notif:user:{tid}:hospital",
        until_ts + 300,
    )
    task.forget()

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Notification Queued",
                    "description": f"The selected notification has been enqueued for <t:{until_ts}:R>.",
                    "color": SKYNET_GOOD,
                    "footer": {
                        "text": f"Task ID: {task.id}",
                    },
                },
            ],
            "flags": 64,
        },
    }
