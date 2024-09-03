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
import json
import random
import typing

if globals().get("orjson:loaded"):
    import orjson

import celery
import requests
from celery.utils.log import get_task_logger
from tornium_commons import Config, DBucket, rds
from tornium_commons.errors import (
    DiscordError,
    MissingKeyError,
    NetworkingError,
    RatelimitError,
    TornError,
)
from tornium_commons.models import TornKey

logger = get_task_logger("celery_app")
config = Config.from_cache()


def backoff(self: celery.Task):
    if self.request.retries <= 1:
        return countdown_wo()
    return int(1 + random.uniform(0, self.request.retries) ** self.request.retries)


def countdown_wo():
    return random.randint(1, 3)


def discord_ratelimit_pre(
    self: celery.Task,
    method: typing.Literal["GET", "PATCH", "POST", "PUT", "DELETE"],
    endpoint: str,
    backoff_var: typing.Optional[bool] = True,
):
    if backoff_var is None:
        backoff_var = True

    try:
        bucket = DBucket.from_endpoint(method=method, endpoint=endpoint)
    except RatelimitError:
        raise self.retry(countdown=backoff(self) if backoff_var else countdown_wo())

    try:
        bucket.call()
    except RatelimitError:
        raise self.retry(countdown=backoff(self) if backoff_var else countdown_wo())

    return bucket


def handle_discord_error(e: DiscordError):
    from tornium_commons.models import Faction, Notification, Server
    from tornium_commons.skyutils import SKYNET_ERROR

    # Channel errors
    if e.code in (
        10003,  # Unknown channel
        50001,  # Missing access
        50013,  # You lack permissions to perform that action
    ) and e.url.startswith("channels/"):
        only_delete = e.code in (10003,)

        try:
            channel_id = int(e.url.split("/")[1])
        except ValueError:
            return

        try:
            webhook_data = requests.post(
                f"https://discord.com/api/v10/channels/{channel_id}/webhooks",
                headers={"Authorization": f'Bot {config["bot_token"]}', "Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "name": "Tornium-Errors",
                        # "avatar": "",
                        # Avatar is a base 64 encoded image using the data URI scheme.
                        # https://discord.com/developers/docs/reference#image-data
                    }
                ),
            ).json()
        except:  # noqa 722
            return

        if "code" in webhook_data:
            return

        guild: typing.Optional[Server] = (
            Server.select(
                Server.verify_log_channel,
                Server.banking_config,
                Server.armory_config,
                Server.assist_channel,
                Server.oc_config,
            )
            .where(Server.sid == webhook_data["guild_id"])
            .first()
        )

        if guild is None:
            return

        db_updates = {}

        if int(guild.verify_log_channel) == channel_id:
            db_updates["verify_log_channel"] = 0

        # TODO: Add handling of attack notif channels

        for banking_faction, banking_config in guild.banking_config.items():
            if int(banking_config.get("channel", 0)) != channel_id:
                continue
            elif "banking_config" not in db_updates:
                db_updates["banking_config"] = guild.banking_config

            db_updates["banking_config"][banking_faction]["channel"] = 0

        for armory_faction, armory_config in guild.armory_config.items():
            if int(armory_config.get("channel", 0)) != channel_id:
                continue
            elif "armory_config" not in db_updates:
                db_updates["armory_config"] = guild.armory_config

            db_updates["armory_config"][armory_faction]["channel"] = 0

        if int(guild.assist_channel) == channel_id:
            db_updates["assist_channel"] = 0

        for oc_faction, oc_config in guild.oc_config.items():
            for oc_n_type, oc_n_config in oc_config.items():
                if int(oc_n_config.get("channel", 0)) != channel_id:
                    continue
                elif "oc_config" not in db_updates:
                    db_updates["oc_config"] = guild.oc_config

                db_updates["oc_config"][oc_faction][oc_n_type]["channel"] = 0

        if len(db_updates) != 0:
            Server.update(**db_updates).where(Server.sid == webhook_data["guild_id"]).execute()

        Faction.update(od_channel=0).where(Faction.od_channel == channel_id).execute()
        Notification.update(enabled=False).where(
            (Notification.recipient == channel_id) & (Notification.recipient_guild != 0)
        ).execute()

        if only_delete:
            return

        payload = {
            "embeds": [
                {
                    "title": "Channel Error",
                    "description": (
                        "Failed to perform an action in this channel (most likely send a notification) "
                        "due to an error from Discord. The configuration that has failed has been disabled/deleted, "
                        "once you fix this issue, you can re-enable the feature on the bot dashboard."
                    ),
                    "color": SKYNET_ERROR,
                },
            ],
        }

        if e.code == 50001:
            payload["embeds"][0][
                "description"
            ] += " The bot most likely is unable to see this channel. Make sure that the bot has read permissions for this channel."
        elif e.code == 50013:
            payload["embeds"][0]["description"] += " The bot most likely is unable to write to this channel."

        try:
            requests.post(
                f"https://discord.com/api/v10/webhooks/{webhook_data['id']}/{webhook_data['token']}",
                headers={"Authorization": f'Bot {config["bot_token"]}', "Content-Type": "application/json"},
                data=json.dumps(payload),
            )
            requests.delete(
                f"https://discord.com/api/v10/webhooks/{webhook_data['id']}",
                headers={"Authorization": f'Bot {config["bot_token"]}', "Content-Type": "application/json"},
            )
        except:  # noqa 722
            pass


@celery.shared_task(name="tasks.api.tornget", time_limit=5, routing_key="api.tornget", queue="api")
def tornget(endpoint, key, tots=0, fromts=0, stat="", session=None, pass_error=False, version=1):
    url = (
        f'{config.torn_api_uri}v{version}/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}'
        f'{"" if tots == 0 else f"&to={tots}"}{stat if stat == "" else f"&stat={stat}"}'
    )

    if key is None or key == "":
        raise MissingKeyError

    redis_client = rds()
    redis_key = f"tornium:torn-ratelimit:{key}"
    ttl = 60 - datetime.datetime.utcnow().second

    redis_client.set(redis_key, 50, nx=True, ex=ttl)

    try:
        if int(redis_client.get(redis_key)) > 0:
            redis_client.decrby(redis_key, 1)
            redis_client.expire(redis_key, ttl, nx=True)
        else:
            if redis_client.ttl(redis_key) == -1:
                redis_client.set(redis_key, 1, ex=ttl)

            raise RatelimitError
    except TypeError:
        redis_client.set(redis_key, 50, nx=True, ex=ttl)

    try:
        if session is None:
            request = requests.get(url, timeout=5)
        else:
            request = session.get(url, timeout=5)
    except requests.exceptions.Timeout:
        raise NetworkingError(code=408, url=url)

    if request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    if globals().get("orjson:loaded"):
        request = orjson.loads(request.content)
    else:
        request = request.json()

    if "error" in request:
        if request["error"]["code"] in (
            2,  # Incorrect key
            10,  # Key owner is in federal jail
            13,  # Key disabled due to owner inactivity
            18,  # API key paused by owner
        ):
            # TODO: Add proper support for pausing API key with restoring when the key has been unpaused
            #
            # Delete the API key
            # WIth these errors, it'll hurt more to keep the API key rather than removing it and letting the person sign in later
            TornKey.delete().where(TornKey.api_key == key).execute()

        if not pass_error:
            raise TornError(code=request["error"]["code"], endpoint=url)

    return request


@celery.shared_task(
    name="tasks.api.discordget",
    bind=True,
    max_retries=5,
    routing_key="api.discordget",
    queue="api",
    time_limit=10,
)
def discordget(self: celery.Task, endpoint, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {"Authorization": f'Bot {config["bot_token"]}'}

    bucket = discord_ratelimit_pre(self, "GET", endpoint, backoff_var=kwargs.get("backoff", True))
    request = requests.get(url, headers=headers)
    bucket.update_bucket(request.headers, "GET", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(),
            exc=RatelimitError(),
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        handle_discord_error(error)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(
    name="tasks.api.discordpatch",
    bind=True,
    max_retries=5,
    routing_key="api.discordpatch",
    queue="api",
    time_limit=10,
)
def discordpatch(self, endpoint, payload, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {config["bot_token"]}',
        "Content-Type": "application/json",
    }

    bucket = discord_ratelimit_pre(self, "PATCH", endpoint, backoff_var=kwargs.get("backoff", True))

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    request = requests.patch(url, headers=headers, data=payload)
    bucket.update_bucket(request.headers, "PATCH", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(),
            exc=RatelimitError(),
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        handle_discord_error(error)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(
    name="tasks.api.discordpost",
    bind=True,
    max_retries=5,
    routing_key="api.discordpost",
    queue="api",
    time_limit=10,
)
def discordpost(self, endpoint, payload, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {config["bot_token"]}',
        "Content-Type": "application/json",
    }

    bucket = discord_ratelimit_pre(self, "POST", endpoint, backoff_var=kwargs.get("backoff", True))

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    request = requests.post(url, headers=headers, data=payload)
    bucket.update_bucket(request.headers, "POST", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(),
            exc=RatelimitError(),
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        handle_discord_error(error)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(
    name="tasks.api.discordput",
    bind=True,
    max_retries=5,
    routing_key="api.discordput",
    queue="api",
)
def discordput(self, endpoint, payload, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {config["bot_token"]}',
        "Content-Type": "application/json",
    }

    bucket = discord_ratelimit_pre(self, "PUT", endpoint, backoff_var=kwargs.get("backoff", True))

    if globals().get("orjson:loaded"):
        payload = orjson.dumps(payload)
    else:
        payload = json.dumps(payload)

    request = requests.put(url, headers=headers, data=payload)
    bucket.update_bucket(request.headers, "PUT", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(),
            exc=RatelimitError(),
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        handle_discord_error(error)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(
    name="tasks.api.discorddelete",
    bind=True,
    max_retries=5,
    routing_key="api.discorddelete",
    queue="api",
    time_limit=5,
)
def discorddelete(self, endpoint, *args, **kwargs):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {
        "Authorization": f'Bot {config["bot_token"]}',
        "Content-Type": "application/json",
    }

    bucket = discord_ratelimit_pre(self, "GET", endpoint, backoff_var=kwargs.get("backoff", True))
    request = requests.delete(url, headers=headers)
    bucket.update_bucket(request.headers, "DELETE", endpoint)

    if request.status_code == 429:
        raise self.retry(
            countdown=backoff(self) if kwargs.get("backoff", True) else countdown_wo(),
            exc=RatelimitError(),
        )

    try:
        if globals().get("orjson:loaded"):
            request_json = orjson.loads(request.content)
        else:
            request_json = request.json()
    except Exception as e:
        if request.status_code // 100 != 2:
            raise NetworkingError(code=request.status_code, url=url)
        elif request.status_code == 204:
            return
        else:
            raise e

    if "code" in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a full list of error codes
        # explanations

        if request_json["code"] == 0:
            logger.info(request_json)

        error = DiscordError(code=request_json["code"], message=request_json["message"], url=endpoint)
        handle_discord_error(error)
        raise error
    elif request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    return request_json


@celery.shared_task(
    name="tasks.api.torn_stats_get",
    time_limit=15,
    routing_key="api.torn_stats_get",
    queue="api",
)
def torn_stats_get(endpoint, key, session=None):
    url = f"https://www.tornstats.com/api/v2/{key}/{endpoint}"
    redis_key = f"tornium:ts-ratelimit:{key}"
    redis_client = rds()

    redis_client.set(redis_key, 15, nx=True, ex=60 - datetime.datetime.utcnow().second)

    if redis_client.ttl(redis_key) < 1:
        redis_client.expire(redis_key, 1)
        redis_client.set(redis_key, 50, nx=True, ex=60 - datetime.datetime.utcnow().second)

    if int(redis_client.get(redis_key)) > 0:
        redis_client.decrby(redis_key, 1)
    else:
        raise RatelimitError

    try:
        if session is None:
            request = requests.get(url, timeout=15)
        else:
            request = session.get(url, timeout=15)
    except requests.exceptions.Timeout:
        raise NetworkingError(code=408, url=url)

    if request.status_code // 100 != 2:
        raise NetworkingError(code=request.status_code, url=url)

    if globals().get("orjson:loaded"):
        request = orjson.loads(request.content)
    else:
        request = request.json()

    return request
