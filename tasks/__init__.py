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

from gevent import monkey

monkey.patch_all()

import importlib.util
import sys

for module in ("ddtrace", "orjson"):
    try:
        globals()[f"{module}:loaded"] = bool(importlib.util.find_spec(module))
    except (ValueError, ModuleNotFoundError):
        globals()[f"{module}:loaded"] = False


if globals().get("ddtrace:loaded") and not hasattr(sys, "_called_from_test"):
    from ddtrace import patch_all

    patch_all(logging=True)

import json
import logging
import typing

import kombu
from celery import Celery
from celery.schedules import crontab
from mongoengine import connect
from mongoengine.queryset import QuerySet

from models.factionmodel import FactionModel
from models.factionstakeoutmodel import FactionStakeoutModel
from models.notificationmodel import NotificationModel
from models.servermodel import ServerModel
from models.userstakeoutmodel import UserStakeoutModel
from utils.config import Config

config = Config().load()

if not hasattr(sys, "_called_from_test"):
    connect(
        db="Tornium",
        username=config["username"],
        password=config["password"],
        host=f'mongodb://{config["host"]}',
        connect=False,
    )

FORMAT = (
    "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] "
    "[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%"
    "(dd.span_id)s] - %(message)s"
)

celery_app: typing.Optional[Celery] = None
logger: logging.Logger = logging.getLogger("celeryerrors")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="celeryerrors.log", encoding="utf-8", mode="a")
handler.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(handler)


if celery_app is None:
    try:
        file = open("celery.json")
        file.close()
    except FileNotFoundError:
        data = {  # Faction tasks
            "refresh-factions": {
                "task": "tasks.faction.refresh_factions",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "5", "hour": "*"},
            },
            "fetch-attacks-runner": {
                "task": "tasks.faction.fetch_attacks_runner",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },
            "oc-refresh": {
                "task": "tasks.faction.oc_refresh",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/5", "hour": "*"},
            },
            "auto-cancel-requests": {
                "tasks": "tasks.faction.auto_cancel_requests",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/10", "hour": "*"},
            },  # Guild tasks
            "refresh-guilds": {
                "task": "tasks.guild.refresh_guilds",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "0", "hour": "*"},
            },
            "user-stakeouts": {
                "task": "tasks.stakeouts.user_stakeouts",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },
            "faction-stakeouts": {
                "task": "tasks.stakeouts.faction_stakeouts",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },  # User tasks
            "refresh-users": {
                "task": "tasks.user.refresh_users",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/10", "hour": "*"},
            },
            "fetch-attacks-user-runner": {
                "task": "tasks.user.fetch_attacks_user_runner",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/5", "hour": "*"},
            },  # Stock tasks
            "fetch-stock-ticks": {
                "task": "tasks.stocks.fetch_stock_ticks",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },
        }

        with open("celery.json", "w") as file:
            json.dump(data, file, indent=4)

    with open("celery.json", "r") as file:
        data = json.load(file)

    celery_app = Celery(
        "tasks",
        backend="redis://localhost:6379/0",
        broker="redis://localhost:6379/0",
        include=[
            "tasks",
            "tasks.api",
            "tasks.faction",
            "tasks.guild",
            "tasks.stakeouts",
            "tasks.stocks",
            "tasks.user",
        ],
    )
    celery_app.conf.update(task_serializer="json", result_serializer="json")
    celery_app.conf.timezone = "UTC"
    celery_app.conf.task_queues = (
        kombu.Queue("default", routing_key="tasks.#"),
        kombu.Queue("quick", routing_key="quick.#"),
        kombu.Queue("api", routing_key="api.#"),
    )
    celery_app.conf.task_default_queue = "default"
    celery_app.conf.task_default_routing_key = "task.default"
    celery_app.conf.task_routes = {
        "tasks.api.tornget": {
            "queue": "api",
            "routing_key": "api.torn",
        },
        "tasks.api.discord*": {
            "queue": "api",
            "routing_key": "api.discord",
        },
        "tasks.api.torn_stats_get": {
            "queue": "api",
            "routing_key": "api.tornstats",
        },
        "tasks.faction.refresh_factions": {
            "queue": "default",
            "routing_key": "tasks.refresh_factions",
        },
        "tasks.faction.fetch_attacks_runner": {
            "queue": "default",
            "routing_key": "tasks.fetch_attacks_runner",
        },
        "tasks.faction.retal_attacks": {
            "queue": "default",
            "routing_key": "quick.retal_attacks",
        },
        "tasks.faction.stat_db_attacks": {
            "queue": "default",
            "routing_key": "quick.stat_db_attacks",
        },
        "tasks.faction.oc_refresh": {
            "queue": "default",
            "routing_key": "tasks.oc_refresh",
        },
        "tasks.faction.auto_cancel_requests": {"queue": "default", "routing_key": "quick.auto_cancel_requests"},
        "tasks.guild.refresh_guilds": {
            "queue": "default",
            "routing_key": "tasks.refresh_guilds",
        },
        "tasks.stocks.fetch_stock_ticks": {
            "queue": "default",
            "routing": "tasks.fetch_stock_ticks",
        },
        "tasks.user.update_user": {
            "queue": "default",
            "routing": "tasks.update_user",
        },
        "tasks.user.refresh_users": {
            "queue": "default",
            "routing": "tasks.refresh_users",
        },
        "tasks.user.fetch_attacks_user_runner": {
            "queue": "quick",
            "routing": "quick.fetch_attacks_user_runner",
        },
        "tasks.user.stat_db_attacks_user": {
            "queue": "default",
            "routing": "tasks.stat_db_attacks_user",
        },
    }

    schedule = {}

    if "refresh-factions" in data and data["refresh-factions"]["enabled"]:
        schedule["refresh-factions"] = {
            "task": data["refresh-factions"]["task"],
            "schedule": crontab(
                minute=data["refresh-factions"]["schedule"]["minute"],
                hour=data["refresh-factions"]["schedule"]["hour"],
            ),
        }
    if "fetch-attacks-runner" in data and data["fetch-attacks-runner"]["enabled"]:
        schedule["fetch-attacks-runner"] = {
            "task": data["fetch-attacks-runner"]["task"],
            "schedule": crontab(
                minute=data["fetch-attacks-runner"]["schedule"]["minute"],
                hour=data["fetch-attacks-runner"]["schedule"]["hour"],
            ),
        }
    if "oc-refresh" in data and data["oc-refresh"]["enabled"]:
        schedule["oc-refresh"] = {
            "task": data["oc-refresh"]["task"],
            "schedule": crontab(
                minute=data["oc-refresh"]["schedule"]["minute"],
                hour=data["oc-refresh"]["schedule"]["hour"],
            ),
        }
    if "auto-cancel-requests" in data and data["auto-cancel-requests"]["enabled"]:
        schedule["auto-cancel-requests"] = {
            "task": data["auto-cancel-requests"]["task"],
            "schedule": crontab(
                minute=data["auto-cancel-requests"]["schedule"]["minute"],
                hour=data["auto-cancel-requests"]["schedule"]["hour"],
            ),
        }
    if "refresh-guilds" in data and data["refresh-guilds"]["enabled"]:
        schedule["refresh-guilds"] = {
            "task": data["refresh-guilds"]["task"],
            "schedule": crontab(
                minute=data["refresh-guilds"]["schedule"]["minute"],
                hour=data["refresh-guilds"]["schedule"]["hour"],
            ),
        }
    if "user-stakeouts" in data and data["user-stakeouts"]["enabled"]:
        schedule["user-stakeouts"] = {
            "task": data["user-stakeouts"]["task"],
            "schedule": crontab(
                minute=data["user-stakeouts"]["schedule"]["minute"],
                hour=data["user-stakeouts"]["schedule"]["hour"],
            ),
        }
    if "faction-stakeouts" in data and data["faction-stakeouts"]["enabled"]:
        schedule["faction-stakeouts"] = {
            "task": data["faction-stakeouts"]["task"],
            "schedule": crontab(
                minute=data["faction-stakeouts"]["schedule"]["minute"],
                hour=data["faction-stakeouts"]["schedule"]["hour"],
            ),
        }
    if "refresh-users" in data and data["refresh-users"]["enabled"]:
        schedule["refresh-users"] = {
            "task": data["refresh-users"]["task"],
            "schedule": crontab(
                minute=data["refresh-users"]["schedule"]["minute"],
                hour=data["refresh-users"]["schedule"]["hour"],
            ),
        }
    if "fetch-attacks-user-runner" in data and data["fetch-attacks-user-runner"]["enabled"]:
        schedule["fetch-attacks-user-runner"] = {
            "task": data["fetch-attacks-user-runner"]["task"],
            "schedule": crontab(
                minute=data["fetch-attacks-user-runner"]["schedule"]["minute"],
                hour=data["fetch-attacks-user-runner"]["schedule"]["hour"],
            ),
        }
    if "fetch-stock-ticks" in data and data["fetch-stock-ticks"]["enabled"]:
        schedule["fetch-stock-ticks"] = {
            "task": data["fetch-stock-ticks"]["task"],
            "schedule": crontab(
                minute=data["fetch-stock-ticks"]["schedule"]["minute"],
                hour=data["fetch-stock-ticks"]["schedule"]["hour"],
            ),
        }

    celery_app.conf.beat_schedule = schedule


@celery_app.task
def remove_unknown_channel(channel_id: int):
    channel_id = int(channel_id)

    faction_vault_channel: QuerySet = FactionModel.objects(vaultconfig__banking=channel_id)
    faction_od_channel: QuerySet = FactionModel.objects(chainconfig__odchannel=channel_id)

    notifications: QuerySet = NotificationModel.objects(target=channel_id)

    server_verify_channel: typing.Optional[ServerModel] = ServerModel.objects(verify_log_channel=channel_id).first()
    server_assist_channel: typing.Optional[ServerModel] = ServerModel.objects(assistschannel=channel_id).first()

    faction: FactionModel
    for faction in faction_vault_channel:
        faction.vaultconfig["banking"] = 0
        faction.save()

    faction: FactionModel
    for faction in faction_od_channel:
        faction.chainod["odchannel"] = 0
        faction.save()

    if notifications.count() > 0:
        notifications.delete()

    if server_verify_channel is not None:
        server_verify_channel.verify_log_channel = 0
        server_verify_channel.save()

    if server_assist_channel is not None:
        server_assist_channel.assistschannel = 0
        server_assist_channel.save()

    faction_stakeout: FactionStakeoutModel
    for faction_stakeout in FactionStakeoutModel.objects():
        faction_stakeout_data = faction_stakeout.guilds

        for guild, guild_stakeout in faction_stakeout.guilds.copy().items():
            if guild_stakeout.get("channel") in (None, 0, channel_id):
                faction_stakeout_data.pop(guild, None)

        faction_stakeout.guilds = faction_stakeout_data

        if len(faction_stakeout.guilds) == 0:
            faction_stakeout.delete()
        else:
            faction_stakeout.save()

    user_stakeout: UserStakeoutModel
    for user_stakeout in UserStakeoutModel.objects():
        user_stakeout_data = user_stakeout.guilds

        for guild, guild_stakeout in user_stakeout.guilds.copy().items():
            if guild_stakeout.get("channel") in (None, 0, channel_id):
                user_stakeout_data.pop(guild, None)

        user_stakeout.guilds = user_stakeout_data

        if len(user_stakeout.guilds) == 0:
            user_stakeout.delete()
        else:
            user_stakeout.save()

    server: ServerModel
    for server in ServerModel.objects():
        for faction_id, faction_oc in server.oc_config.copy().items():
            if int(faction_oc["ready"]["channel"]) == channel_id:
                server.oc_config[faction_id]["ready"]["channel"] = 0
            if int(faction_oc["delay"]["channel"]) == channel_id:
                server.oc_config[faction_id]["delay"]["channel"] = 0

        server.save()


@celery_app.task
def remove_unknown_role(role_id: int):
    role_id = int(role_id)

    faction_vault_role: QuerySet = FactionModel.objects(vaultconfig__banker=role_id)

    server_verify_roles: typing.Optional[ServerModel] = ServerModel.objects(verified_roles=role_id).first()

    faction: FactionModel
    for faction in faction_vault_role:
        faction.vaultconfig["banker"] = 0
        faction.save()

    server: ServerModel
    for server in server_verify_roles:
        server.verified_roles.remove(role_id)
        server.save()

    server: ServerModel
    for server in ServerModel.objects():
        server_verify = server.faction_verify

        for faction_id, faction_verify in server.faction_verify.copy().items():
            if role_id in faction_verify["roles"]:
                server_verify[faction_id]["roles"].remove(role_id)

        server.faction_verify = server_verify
        server_oc_config = server.oc_config

        for faction_id, faction_oc in server.oc_config.copy().items():
            if str(role_id) in faction_oc["ready"]["roles"]:
                server_oc_config[faction_id]["ready"]["roles"].remove(str(role_id))
            if str(role_id) in faction_oc["delay"]["roles"]:
                server_oc_config[faction_id]["delay"]["roles"].remove(str(role_id))

        server.oc_config = server_oc_config
        server.save()
