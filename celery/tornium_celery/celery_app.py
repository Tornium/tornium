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

import importlib.util
import sys

for module in ("ddtrace", "orjson"):
    try:
        globals()[f"{module}:loaded"] = bool(importlib.util.find_spec(module))
    except (ValueError, ModuleNotFoundError):
        globals()[f"{module}:loaded"] = False


if globals().get("ddtrace:loaded") and not hasattr(sys, "_called_from_test"):
    try:
        from ddtrace import patch_all

        patch_all(logging=True)
    except ImportError:
        globals()["ddtrace:loaded"] = False

import json
import typing

import kombu
from tornium_commons import Config

from celery import Celery
from celery.app import trace
from celery.schedules import crontab
from celery.signals import after_setup_logger

config = Config.from_json()

_FORMAT = (
    "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] "
    "[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%"
    "(dd.span_id)s] - %(message)s"
)
_LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "datadog": {
            "format": _FORMAT,
        },
        "simple": {
            "format": "%(asctime)s %(levelname)s [%(name)s] - %(message)s",
        },
        "expanded": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        },
    },
    "handlers": {
        "celery_handler": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "celery.log",
            "formatter": "datadog" if globals()["ddtrace:loaded"] else "expanded",
        },
        "console_handler": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "celery_app": {
            "handlers": ["celery_handler", "console_handler"],
            "level": "DEBUG",
        }
    },
}


celery_app: typing.Optional[Celery] = None


@after_setup_logger.connect
def config_loggers(logger, *args, **kwargs):
    from logging.config import dictConfig

    dictConfig(_LOGGING)


if celery_app is None:
    try:
        file = open("celery.json")
        file.close()
    except FileNotFoundError:
        beat_data = {  # Faction tasks
            "refresh-factions": {
                "task": "tasks.faction.refresh_factions",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "5", "hour": "*"},
            },
            "fetch-attacks-runner": {
                "task": "tasks.faction.fetch_attacks_runner",
                "enabled": True,
                "schedule": {"type": "periodic", "second": "10"},
            },
            "oc-refresh": {
                "task": "tasks.faction.oc_refresh",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/5", "hour": "*"},
            },
            "armory-check": {
                "task": "tasks.faction.armory_check",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "0", "hour": "*"},
            },
            "auto-cancel-requests": {
                "task": "tasks.faction.auto_cancel_requests",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/10", "hour": "*"},
            },
            "check-assists": {
                "task": "tasks.faction.check_assists",
                "enabled": True,
                "schedule": {"type": "periodic", "second": "30"},
            },  # Guild tasks
            "refresh-guilds": {
                "task": "tasks.guild.refresh_guilds",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "0", "hour": "*"},
            },
            "verify-guilds": {
                "task": "tasks.guild.verify_guilds",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/15", "hour": "*"},
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
            },
            "check-api-keys": {
                "task": "tasks.user.check_api_keys",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },  # Stock tasks
            "stocks-prefetch": {
                "task": "tasks.stocks.stocks_prefetch",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },  # Stakeout hooks/tasks
            "run-user-stakeouts": {
                "task": "tasks.stakeout_hooks.run_user_stakeouts",
                "enabled": False,
                "schedule": {"type": "periodic", "second": "30"},
            },
            "run-faction-stakeouts": {
                "task": "tasks.stakeout_hooks.run_faction_stakeouts",
                "enabled": False,
                "schedule": {"type": "periodic", "second": "30"},
            },  # Item tasks
            "update-items": {
                "task": "tasks.items.update_items",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "0", "hour": "*/4"},
            },
            "fetch-market": {
                "task": "tasks.items.fetch_market",
                "enabled": True,
                "schedule": {"type": "periodic", "second": "30"},
            },
        }

        with open("celery.json", "w") as file:
            json.dump(beat_data, file, indent=4)

    with open("celery.json", "r") as file:
        beat_data: dict = json.load(file)

    celery_app = Celery(
        "tasks",
        backend="redis://localhost:6379/0",
        broker="redis://localhost:6379/0",
        include=[
            "tasks.api",
            "tasks.faction",
            "tasks.guild",
            "tasks.items",
            "tasks.misc",
            "tasks.reports",
            "tasks.stakeout_hooks",
            "tasks.stocks",
            "tasks.user",
        ],
    )
    celery_app.conf.update(task_serializer="json", result_serializer="json")
    celery_app.conf.timezone = "UTC"
    celery_app.conf.task_queues = (
        kombu.Queue("default", routing_key="default.#"),
        kombu.Queue("quick", routing_key="quick.#"),
        kombu.Queue("api", routing_key="api.#"),
    )
    celery_app.conf.task_default_queue = "default"
    schedule = {}

    task_data: dict
    for task_name, task_data in beat_data.items():
        if not task_data.get("enabled"):
            continue
        elif task_data.get("schedule") is None:
            continue
        elif task_data["schedule"].get("type") not in ("cron", "periodic"):
            continue

        if task_data["schedule"]["type"] == "periodic":
            _s: typing.Union[int, str] = task_data["schedule"].get("second")

            if _s is None or (not isinstance(_s, int) and not _s.isdigit()):
                continue

            s = int(_s)
        elif task_data["schedule"]["type"] == "cron":
            _m: str = task_data["schedule"].get("minute")
            _h: str = task_data["schedule"].get("hour")

            if _m is None or _h is None:
                continue

            s = crontab(minute=_m, hour=_h)
        else:
            continue

        schedule[task_name] = {"task": task_data["task"], "schedule": s}

    celery_app.conf.beat_schedule = schedule
    celery_app.conf.result_expires = 300  # Results are evicted from Redis cache after five minutes
    celery_app.set_default()

    trace.LOG_SUCCESS = """\
    Task %(name)s[%(id)s] succeeded in %(runtime)ss
    """
