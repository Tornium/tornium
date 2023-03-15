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

import time
import typing

from mongoengine import QuerySet
from mongoengine.queryset.visitor import Q

from tornium_commons.formatters import find_list
from tornium_commons.models import FactionModel, NotificationModel, ServerModel, UserModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO

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
    },
}


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

        passed_scat = find_list(subcommand_data, "name", "category")[1]["value"].lower()
        notification: NotificationModel = notifications.first()

        if notification.ntype == 1:
            scat_id = _SCATS["user"][passed_scat]
        elif notification.ntype == 2:
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

        # notification.value: list or ListField
        if scat_id in notification.value:
            values = list(notification.value)
            values.remove(scat_id)
            notification.value = values
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
                                "text": f"DB ID: {notification.id}",
                            },
                        }
                    ]
                },
            }
        else:
            values = list(notification.value)
            values.append(scat_id)
            notification.value = values
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
                                "text": f"DB ID: {notification.id}",
                            },
                        }
                    ]
                },
            }

    def delete():
        notification: NotificationModel = notifications.first()
        notification.delete()

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": f"Notification Deleted",
                        "description": f"The first specified notification has been deleted.",
                        "color": SKYNET_GOOD,
                        "footer": {
                            "text": f"DB ID: {notification.id}",
                        },
                    }
                ]
            },
        }

    def info():
        embeds = []

        notification: NotificationModel
        for notification in notifications:
            if notification.ntype == 1:
                notification_object: typing.Optional[UserModel] = UserModel.objects(tid=notification.target).first()
                title = "User Stakeout"
            else:
                notification_object: typing.Optional[FactionModel] = FactionModel.objects(
                    tid=notification.target
                ).first()
                title = "Faction Stakeout"

            if len(notification.value) == 0:
                categories = "None"
            else:
                categories = ", ".join(
                    [_REVERSE_SCATS[_REVERSE_STYPE_NID_MAP[notification.ntype]][value] for value in notification.value]
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
                            "value": notification.options["enabled"],
                            "inline": True,
                        },
                        {  # Newline in fields
                            "name": "\u200B",
                            "value": "\u200B",
                            "inline": True,
                        },
                        {
                            "name": "Private",
                            "value": not bool(notification.recipient_type),
                            "inline": True,
                        },
                        {
                            "name": "Target Channel",
                            "value": f"<#{notification.recipient}>"
                            if notification.recipient_type == 1
                            else "Direct Message",
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": f"DB ID: {notification.id}",
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
        private = find_list(subcommand_data, "name", "private")
        channel = find_list(subcommand_data, "name", "channel")

        if private == -1:
            private = True
        else:
            private = private[1]["value"]

        if channel == -1:
            channel = None
        else:
            channel = channel[1]["value"]

        if not private and channel is None:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Illegal Command Input",
                            "description": "The notification can not be public without a channel provided.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }
        elif private and user.discord_id == 0:
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
            guild: ServerModel = ServerModel.objects(sid=interaction["guild_id"]).first()

            if guild is None:
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
            elif user.tid not in guild.admins:
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
                NotificationModel.objects(
                    Q(invoker=user.tid)
                    & Q(recipient=user.discord_id)
                    & Q(recipient_type=0)
                    & Q(target=tid)
                    & Q(ntype=_STYPE_NID_MAP[stype])
                ).count()
                > 0
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
                NotificationModel.objects(
                    Q(recipient=int(interaction["guild_id"]))
                    & Q(recipient_type=1)
                    & Q(target=tid)
                    & Q(ntype=_STYPE_NID_MAP[stype])
                ).count()
                > 0
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

        notification = NotificationModel(
            invoker=user.tid,
            time_created=int(time.time()),
            recipient=user.discord_id if private else channel,
            recipient_guild=int(interaction["guild_id"]) if not private else 0,
            recipient_type=int(not private),
            ntype=_STYPE_NID_MAP[stype],
            target=tid,
            persistent=True,
            value=[],
            options={
                "enabled": False,
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
                                "value": not bool(notification.recipient_type),
                                "inline": True,
                            },
                            {
                                "name": "Target Channel",
                                "value": f"<#{notification.recipient}>"
                                if notification.recipient_type == 1
                                else "Direct Message",
                                "inline": True,
                            },
                        ],
                        "footer": {
                            "text": f"DB ID: {notification.id}",
                        },
                    }
                ]
            },
        }

    def list_notfs():
        notifications: QuerySet
        if "guild_id" in interaction:
            notifications = NotificationModel.objects(
                Q(recipient_type=1)
                & (Q(recipient_guild=int(interaction["guild_id"])) | (Q(recipient_guild=0) & Q(invoker=user.tid)))
            )
        else:
            notifications = NotificationModel.objects(Q(recipient_type=0) & Q(recipient_guild=0) & Q(invoker=user.tid))

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

        notification: NotificationModel
        for notification in notifications:
            if notification.recipient_type == 0:
                payload["data"]["embeds"][0][
                    "description"
                ] += f"\n{_REVERSE_STYPE_NID_MAP[notification.ntype]} stakeout on {notification.target} - DM"
            else:
                payload["data"]["embeds"][0][
                    "description"
                ] += f"\n{_REVERSE_STYPE_NID_MAP[notification.ntype]} stakeout on {notification.target} - <#{notification.recipient}>"

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

        notification: NotificationModel = notifications.first()

        if mode == "enable":
            mode_bool = True
        else:
            mode_bool = False

        if notification.options.get("enabled") == mode_bool:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": f"Stakeout Issue",
                            "description": f"Stakeout is already {mode}d.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        notification.options["enabled"] = mode_bool
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

    user: UserModel = kwargs["invoker"]

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

    if tid == -1:
        tid = None
    else:
        tid = tid[1]["value"]

    if stype == -1:
        stype = None
    else:
        stype = stype[1]["value"]

    if subcommand not in ("initialize", "list"):
        if "guild_id" in interaction:
            guild: ServerModel = ServerModel.objects(sid=interaction["guild_id"]).first()

            if guild is None:
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
            elif user.tid not in guild.admins:
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

        notifications: QuerySet = NotificationModel.objects(target=tid)

        if stype is not None:
            notifications.filter(ntype=_STYPE_NID_MAP[stype])

        if "guild_id" in interaction:
            notifications.filter(
                Q(recipient_type=1)
                & (Q(recipient_guild=int(interaction["guild_id"])) | (Q(recipient_guild=0) & Q(invoker=user.tid)))
            )
        else:
            notifications.filter(Q(recipient_type=0) & Q(recipient_guild=0) & Q(invoker=user.tid))

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
