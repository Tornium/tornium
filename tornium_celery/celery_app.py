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

try:
    from gevent import monkey

    globals()["gevent:loaded"] = True
except ImportError:
    globals()["gevent:loaded"] = False

for module in ("ddtrace", "orjson"):
    if globals()["gevent:loaded"] and monkey.is_anything_patched():
        globals()["ddtrace:loaded"] = False
        globals()["orjson:loaded"] = False
        break

    try:
        globals()[f"{module}:loaded"] = bool(importlib.util.find_spec(module))
    except (ValueError, ModuleNotFoundError):
        globals()[f"{module}:loaded"] = False


if globals().get("ddtrace:loaded") and not hasattr(sys, "_called_from_test"):
    try:
        from ddtrace import patch_all

        patch_all(logging=True, pymongo=True, mongoengine=True)
    except ImportError:
        globals()["ddtrace:loaded"] = False

import json
import typing

import kombu
from celery import Celery
from celery.app import trace
from celery.schedules import crontab
from celery.signals import after_setup_logger
from mongoengine import connect
from tornium_commons import Config

config = Config().load()

if not hasattr(sys, "_called_from_test"):
    connect(
        db="Tornium",
        username=config["username"],
        password=config["password"],
        host=f'mongodb://{config["host"]}',
        connect=False,
    )

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
                "task": "tasks.faction.auto_cancel_requests",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*/10", "hour": "*"},
            },  # Guild tasks
            "refresh-guilds": {
                "task": "tasks.guild.refresh_guilds",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "0", "hour": "*"},
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
            "stocks-prefetch": {
                "task": "tasks.stocks.stocks_prefetch",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },  # Stakeout hooks/tasks
            "run-user-stakeouts": {
                "task": "tasks.stakeout_hooks.run_user_stakeouts",
                "enabled": False,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },
            "run-faction-stakeouts": {
                "task": "tasks.stakeout_hooks.run_faction_stakeouts",
                "enabled": False,
                "schedule": {"type": "cron", "minute": "*", "hour": "*"},
            },  # Item tasks
            "update-items": {
                "task": "tasks.items.update_items_pre",
                "enabled": True,
                "schedule": {"type": "cron", "minute": "0", "hour": "*/4"},
            },
            "fetch-market": {
                "task": "tasks.items.fetch_market",
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
            "tasks.api",
            "tasks.faction",
            "tasks.guild",
            "tasks.items",
            "tasks.misc",
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
    if "stocks-prefetch" in data and data["stocks-prefetch"]["enabled"]:
        schedule["stocks-prefetch"] = {
            "task": data["stocks-prefetch"]["task"],
            "schedule": crontab(
                minute=data["stocks-prefetch"]["schedule"]["minute"],
                hour=data["stocks-prefetch"]["schedule"]["hour"],
            ),
        }
    if "run-user-stakeouts" in data and data["run-user-stakeouts"]["enabled"]:
        schedule["run-user-stakeouts"] = {
            "task": data["run-user-stakeouts"]["task"],
            "schedule": crontab(
                minute=data["run-user-stakeouts"]["schedule"]["minute"],
                hour=data["run-user-stakeouts"]["schedule"]["hour"],
            ),
        }
    if "run-faction-stakeouts" in data and data["run-faction-stakeouts"]["enabled"]:
        schedule["run-faction-stakeouts"] = {
            "task": data["run-faction-stakeouts"]["task"],
            "schedule": crontab(
                minute=data["run-faction-stakeouts"]["schedule"]["minute"],
                hour=data["run-faction-stakeouts"]["schedule"]["hour"],
            ),
        }
    if "update-items" in data and data["update-items"]["enabled"]:
        schedule["update-items"] = {
            "task": data["update-items"]["task"],
            "schedule": crontab(
                minute=data["update-items"]["schedule"]["minute"],
                hour=data["update-items"]["schedule"]["hour"],
            ),
        }
    if "fetch-market" in data and data["fetch-market"]["enabled"]:
        schedule["fetch-market"] = {
            "task": data["fetch-market"]["task"],
            "schedule": crontab(
                minute=data["fetch-market"]["schedule"]["minute"],
                hour=data["fetch-market"]["schedule"]["hour"],
            ),
        }

    celery_app.conf.beat_schedule = schedule
    celery_app.conf.result_expires = 300  # Results are evicted from Redis cache after five minutes
    celery_app.set_default()

    trace.LOG_SUCCESS = """\
    Task %(name)s[%(id)s] succeeded in %(runtime)ss
    """
