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


def stakeouts(interaction, *args, **kwargs):
    def info():
        notifications: QuerySet = NotificationModel.objects(target=tid)

        if stype is not None:
            notifications.filter(ntype=_STYPE_NID_MAP[stype])

        if notifications.count() > 1:
            if "guild_id" in interaction:
                notifications.filter(Q(recipient_type=1) & Q(recipient_guild=int(interaction["guild_id"])))
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
                            "value": ", ".join(notification.value) if len(notification.value) > 0 else "None",
                            "inline": True,
                        },
                        {
                            "name": "Enabled",
                            "value": notification.options["enabled"],
                            "inline": True,
                        },
                        {
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

        notification = NotificationModel(
            invoker=user.tid,
            time_created=int(time.time()),
            recipient=user.discord_id if private else channel,
            recipient_guild=int(interaction["guild_id"]) if "guild_id" in interaction else 0,
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

    tid = find_list(subcommand_data, "name", "tid")[1]["value"]
    stype = find_list(subcommand_data, "name", "type")

    if stype == -1:
        stype = None
    else:
        stype = stype[1]["value"]

    if subcommand != "initialize":
        pass

    if subcommand == "category":
        pass
    elif subcommand == "delete":
        pass
    elif subcommand in ("enable", "disable"):
        pass
    elif subcommand == "info":
        return info()
    elif subcommand == "initialize":
        return initialize()
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
