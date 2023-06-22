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
import math
import random
import re
import time
import typing

import celery
from mongoengine import QuerySet
from mongoengine.queryset.visitor import Q
from tornium_commons import rds
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.formatters import (
    rel_time,
    remove_html,
    str_matches,
    torn_timestamp,
)
from tornium_commons.models import NotificationModel, ServerModel, UserModel
from tornium_commons.skyutils import SKYNET_INFO

from .api import discordpost, tornget

_TRAVEL_DESTINATIONS = {
    # Destination: [Standard, Airstrip, WLT, BCT]
    "Mexico": [1560, 1080, 780, 480],
    "Cayman Islands": [2100, 1500, 1080, 660],
    "Canada": [2460, 1740, 1200, 720],
    "Hawaii": [8040, 5460, 4020, 2400],
    "United Kingdom": [9540, 6660, 4800, 2880],
    "Argentina": [10020, 7020, 4980, 3000],
    "Switzerland": [10500, 7380, 5280, 3180],
    "Japan": [13500, 9480, 6780, 4080],
    "China": [14520, 10140, 7260, 4320],
    "UAE": [16260, 11400, 8100, 4860],
    "South Africa": [17820, 12480, 8940, 5340],
}


def send_notification(notification: NotificationModel, payload: dict):
    if not notification.options["enabled"]:
        return

    if notification.recipient_type == 0:
        try:
            dm_channel = int(rds().get(f"tornium:discord:dm:{notification.recipient}"))
        except TypeError:
            try:
                dm_channel = discordpost(
                    "users/@me/channels",
                    payload={
                        "recipient_id": notification.recipient,
                    },
                )

                dm_channel = dm_channel["id"]
                rds().set(f"tornium:discord:dm:{notification.recipient}", dm_channel, nx=True, ex=86400)
            except DiscordError:
                return
            except NetworkingError:
                return

        discordpost.delay(endpoint=f"channels/{dm_channel}/messages", payload=payload).forget()
    elif notification.recipient_type == 1:
        discordpost.delay(
            endpoint=f"channels/{notification.recipient}/messages",
            payload=payload,
            channel=notification.recipient,
        ).forget()
    else:
        return

    if not notification.persistent:
        notification.delete()


def get_destination(status_description: str):
    if status_description.startswith("Traveling"):
        return " ".join(status_description.split(" ")[2:])
    elif status_description.startswith("Returning"):
        return " ".join(status_description.split(" ")[4:])
    else:
        raise AttributeError


def first_landing(duration):
    return torn_timestamp(int(time.time()) + math.ceil(duration * 0.97))


@celery.shared_task(
    name="tasks.stakeout_hooks.run_user_stakeouts", routing_key="quick.stakeouts.run_user", queue="quick"
)
def run_user_stakeouts():
    notifications: QuerySet = NotificationModel.objects(Q(ntype=1) & Q(options__enabled=True))

    notification: NotificationModel
    for notification in notifications:
        invoker: UserModel = UserModel.objects(tid=notification.invoker).first()

        if invoker is None or invoker.key in ("", None):
            if notification.recipient_type == 1:
                guild: ServerModel = ServerModel.objects(sid=notification.recipient_guild).first()

                if guild is None or len(guild.admins) == 0:
                    continue

                key_user: UserModel = UserModel.objects(tid=random.choice(guild.admins)).first()

                if key_user is None:
                    continue

                key = key_user.key
            else:
                continue
        else:
            key = invoker.key

        if key in ("", None):
            continue

        tornget.signature(
            kwargs={
                "endpoint": f"user/{notification.target}?selections=",
                "key": key,
            },
            queue="api",
        ).apply_async(expires=300, link=user_hook.s())


@celery.shared_task(name="tasks.stakeout_hooks.user_hook", routing_key="quick.stakeouts.user_hook", queue="quick")
def user_hook(user_data, faction: typing.Optional[int] = None):
    if "player_id" not in user_data:
        return

    if faction is None:
        notifications: QuerySet = NotificationModel.objects(
            Q(target=user_data["player_id"]) & Q(ntype=1) & Q(options__enabled=True)
        )
    else:
        notifications: QuerySet = NotificationModel.objects(Q(target=faction) & Q(ntype=2) & Q(options__enabled=True))

    if notifications.count() == 0:
        return

    redis_key = f"tornium:stakeout-data:user:{user_data['player_id']}"
    redis_client = rds()

    if "name" not in user_data:
        user: UserModel = UserModel.objects(tid=user_data["player_id"]).first()

        if user is None:
            user_data["name"] = "Unknown"
        else:
            user_data["name"] = user.name

    if "last_action" in user_data:
        if 305 < int(time.time()) - user_data["last_action"]["timestamp"] < 355:
            payload = {
                "embeds": [
                    {
                        "title": f"{user_data['name']} Status Change",
                        "description": (
                            f"{user_data['name']} [{user_data['player_id']}] has now been inactive since "
                            f"{rel_time(user_data['last_action']['timestamp'])}"
                        ),
                        "color": SKYNET_INFO,
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": torn_timestamp()},
                    }
                ]
            }

            notification: NotificationModel
            for notification in notifications:
                if faction is None and 1 not in notification.value:
                    continue
                elif faction is not None and 3 not in notification.value:
                    continue
                elif not notification.options["enabled"]:
                    continue

                send_notification(notification, payload)
        elif (
            redis_client.exists(redis_key + ":last_action:timestamp")
            and int(time.time()) - int(redis_client.get(redis_key + ":last_action:timestamp")) > 300
            and int(time.time()) - user_data["last_action"]["timestamp"] <= 300
        ):
            payload = {
                "embeds": [
                    {
                        "title": f"{user_data['name']} Status Change",
                        "description": f"{user_data['name']} [{user_data['player_id']}] is now active.",
                        "color": SKYNET_INFO,
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": torn_timestamp()},
                    }
                ]
            }

            notification: NotificationModel
            for notification in notifications:
                if faction is None and 0 not in notification.value:
                    continue
                elif faction is not None and 2 not in notification.value:
                    continue
                elif not notification.options["enabled"]:
                    continue

                send_notification(notification, payload)

    if "status" in user_data and redis_client.exists(redis_key + ":status:description"):
        description = redis_client.get(redis_key + ":status:description")

        if re.match(r"(Traveling|Returning)", user_data["status"]["description"]) and not re.match(
            r"(Traveling|Returning)", description
        ):
            destination_durations = _TRAVEL_DESTINATIONS[get_destination(user_data["status"]["description"])]
            payload = {
                "embeds": [
                    {
                        "title": f"{user_data['name']} is Flying",
                        "description": (
                            f"{user_data['name']} [{user_data['player_id']}] is now "
                            f"{user_data['status']['description'][0].lower() + user_data['status']['description'][1:]}."
                        ),
                        "color": SKYNET_INFO,
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": torn_timestamp()},
                    }
                ],
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 2,
                                "label": f"Standard: {first_landing(destination_durations[0])}",
                                "custom_id": f"stakeout:flying:{user_data['player_id']}:0:{int(time.time()) + math.ceil(destination_durations[0] * 0.97)}",
                            },
                            {
                                "type": 2,
                                "style": 2,
                                "label": f"Airstrip: {first_landing(destination_durations[1])}",
                                "custom_id": f"stakeout:flying:{user_data['player_id']}:1:{int(time.time()) + math.ceil(destination_durations[1] * 0.97)}",
                            },
                        ],
                    },
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 2,
                                "label": f"WLT: {first_landing(destination_durations[2])}",
                                "custom_id": f"stakeout:flying:{user_data['player_id']}:2:{int(time.time()) + math.ceil(destination_durations[2] * 0.97)}",
                            },
                            {
                                "type": 2,
                                "style": 2,
                                "label": f"BCT: {first_landing(destination_durations[3])}",
                                "custom_id": f"stakeout:flying:{user_data['player_id']}:3:{int(time.time()) + math.ceil(destination_durations[3] * 0.97)}",
                            },
                        ],
                    },
                ],
            }

            notification: NotificationModel
            for notification in notifications:
                if faction is None and 2 not in notification.value:
                    continue
                elif faction is not None and 4 not in notification.value:
                    continue
                elif not notification.options["enabled"]:
                    continue

                send_notification(notification, payload)
        elif not re.match(r"(Traveling|Returning)", user_data["status"]["description"]) and re.match(
            r"(Traveling|Returning)", description
        ):
            if user_data["status"]["state"] != "Abroad":
                description_suffix = "has returned to Torn"
            else:
                description_suffix = f"has landed in {user_data['status']['description'][3:]}"

            payload = {
                "embeds": [
                    {
                        "title": f"{user_data['name']} has Landed",
                        "description": f"{user_data['name']} [{user_data['player_id']}] {description_suffix}.",
                        "color": SKYNET_INFO,
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": torn_timestamp()},
                    }
                ]
            }

            notification: NotificationModel
            for notification in notifications:
                if faction is None and 2 not in notification.value:
                    continue
                elif faction is not None and 4 not in notification.value:
                    continue
                elif not notification.options["enabled"]:
                    continue

                send_notification(notification, payload)

        if user_data["status"]["description"] == "Okay" and any(str_matches(description.lower(), ["hospital", "jail"])):
            payload = {
                "embeds": [
                    {
                        "title": f"{user_data['name']} is Okay",
                        "description": (
                            f"{user_data['name']} [{user_data['player_id']}] is now okay after being in the "
                            f"{'hospital' if 'In hospital' in description else 'jail'}."
                        ),
                        "color": SKYNET_INFO,
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": torn_timestamp()},
                    }
                ]
            }

            notification: NotificationModel
            for notification in notifications:
                if faction is None and 3 not in notification.value:
                    continue
                elif faction is not None and 1 not in notification.value:
                    continue
                elif not notification.options["enabled"]:
                    continue

                send_notification(notification, payload)

        if "In hospital" in user_data["status"]["description"] and "In hospital" not in description:
            if any(
                str_matches(
                    user_data["status"]["details"],
                    [
                        "Hospitalized",
                        "Dropped",
                        "Shot",
                        "Mauled",
                        "Taken",
                        "Burned",
                        "Attacked",
                        "Mugged",
                        "Kicked",
                        "Suffering",
                    ],
                    starts=True,
                )
            ):
                payload_description = f"have been {remove_html(user_data['status']['details']).lower()}"
            elif user_data["status"]["details"].startswith("Suffering"):
                # Valid hosp reasons
                # Suffering from an acute hemolytic transfusion reaction
                payload_description = "are suffering from an acute hemolytic transfusion reaction"
            elif user_data["status"]["details"].startswith("Was shot"):
                # Valid hosp reasons
                # Was shot while resisting arrest
                payload_description = user_data["status"]["details"].lower().replace("was shot", "have been shot")
            elif user_data["status"]["details"].startswith("Got"):
                # Valid hosp reasons
                # Got a nasty surprise in the post
                payload_description = user_data["status"]["description"].lower().replace("got", "have gotten")
            else:
                # Valid hosp reasons
                # Overdosed on [Drug]
                # Crashed his [Car]
                # Exploded
                # Lost to [User]
                payload_description = f"have {remove_html(user_data['status']['details']).lower()}"

            payload = {
                "embeds": [
                    {
                        "title": f"{user_data['name']} is Hospitalized",
                        "description": (
                            f"{user_data['name']} [{user_data['player_id']}] has entered the hospital as "
                            f"they {payload_description}."
                        ),
                        "color": SKYNET_INFO,
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": torn_timestamp()},
                    }
                ]
            }

            notification: NotificationModel
            for notification in notifications:
                if faction is None and 4 not in notification.value:
                    continue
                elif faction is not None and 1 not in notification.value:
                    continue
                elif not notification.options["enabled"]:
                    continue

                send_notification(notification, payload)

    if "last_action" in user_data:
        redis_client.set(redis_key + ":last_action:status", user_data["last_action"]["status"], ex=300)
        redis_client.set(redis_key + ":last_action:timestamp", user_data["last_action"]["timestamp"], ex=300)

    if "status" in user_data:
        redis_client.set(redis_key + ":status:description", user_data["status"]["description"], ex=300)
        redis_client.set(redis_key + ":status:state", user_data["status"]["state"], ex=300)
        redis_client.set(redis_key + ":status:until", user_data["status"]["until"], ex=300)


@celery.shared_task(
    name="tasks.stakeout_hooks.run_faction_stakeouts", routing_key="quick.stakeouts.run_faction", queue="quick"
)
def run_faction_stakeouts():
    target: int
    for target in (
        NotificationModel.objects(Q(ntype=2) & Q(options__enabled=True)).only("target").distinct(field="target")
    ):
        notification: NotificationModel = NotificationModel.objects(
            Q(ntype=2) & Q(target=target) & Q(options__enabled=True)
        ).first()

        if notification is None:
            continue

        invoker: UserModel = UserModel.objects(tid=notification.invoker).first()

        if invoker is None or invoker.key in ("", None):
            if notification.recipient_type == 1:
                guild: ServerModel = ServerModel.objects(sid=notification.recipient_guild).first()

                if guild is None or len(guild.admins) == 0:
                    continue

                key_user: UserModel = UserModel.objects(tid=random.choice(guild.admins)).first()

                if key_user is None:
                    continue

                key = key_user.key
            else:
                continue
        else:
            key = invoker.key

        if key in ("", None):
            continue

        tornget.signature(
            kwargs={
                "endpoint": f"faction/{notification.target}?selections=",
                "key": key,
            },
            queue="api",
        ).apply_async(expires=300, link=faction_hook.s())


@celery.shared_task(name="tasks.stakeout_hooks.faction_hook", routing_key="quick.stakeouts.faction_hook", queue="quick")
def faction_hook(faction_data):
    if "ID" not in faction_data:
        return

    notifications: QuerySet = NotificationModel.objects(
        Q(target=faction_data["ID"]) & Q(ntype=2) & Q(options__enabled=True)
    )

    if notifications.count() == 0:
        return

    redis_key = f"tornium:stakeout-data:faction:{faction_data['ID']}"
    redis_client = rds()

    if "members" in faction_data:
        for member_id in redis_client.smembers(f"{redis_key}:members"):
            if str(member_id) not in faction_data["members"].keys():
                redis_client.srem(f"{redis_key}:members", member_id)
                member: typing.Optional[UserModel] = UserModel.objects(tid=int(member_id)).first()

                payload = {
                    "embeds": [
                        {
                            "title": "",
                            "description": "",
                            "color": SKYNET_INFO,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": torn_timestamp()},
                        }
                    ]
                }

                if member is None:
                    payload["embeds"][0]["title"] = "Member Left Faction"
                    payload["embeds"][0][
                        "description"
                    ] = f"Unknown [{member_id}] has left {faction_data['name']} [{faction_data['ID']}]."
                else:
                    payload["embeds"][0]["title"] = f"{member.name} Left Faction"
                    payload["embeds"][0][
                        "description"
                    ] = f"{member.name} [{member_id}] has left {faction_data['name']} [{faction_data['ID']}]."

                notification: NotificationModel
                for notification in notifications:
                    if 0 not in notification.value:
                        continue
                    elif not notification.options["enabled"]:
                        continue

                    send_notification(notification, payload)

        skip_member_notifs = redis_client.scard(f"{redis_key}:members") == 0

        for member_id, member_data in faction_data["members"].items():
            member_data["player_id"] = int(member_id)
            user_hook.delay(member_data, faction_data["ID"]).forget()

            if not redis_client.sismember(f"{redis_key}:members", member_id):
                redis_client.sadd(f"{redis_key}:members", member_id)

                if not skip_member_notifs:
                    payload = {
                        "embeds": [
                            {
                                "title": f"{member_data['name']} Joined Faction",
                                "description": f"{member_data['name']} [{member_data['player_id']}] has joined {faction_data['name']} [{faction_data['ID']}].",
                                "color": SKYNET_INFO,
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": torn_timestamp()},
                            }
                        ]
                    }

                    notification: NotificationModel
                    for notification in notifications:
                        if 0 not in notification.value:
                            continue
                        elif not notification.options["enabled"]:
                            continue

                        send_notification(notification, payload)
