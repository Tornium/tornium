# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
from decimal import Decimal
import re
import sys

import discord
from redis.commands.json.path import Path
import requests

from redisdb import get_redis
from utils.errors import *

sys.path.append("..")


def get_prefix(bot, message):
    if type(message.channel) == discord.DMChannel:
        return "?"

    from models.server import Server

    return Server(message.guild.id).prefix


def text_to_num(text):
    text = text.upper().replace(",", "")
    numbers = re.sub(f"[a-z]", "", text.lower())

    if "K" in text:
        return int(Decimal(numbers) * 1000)
    elif "M" in text:
        return int(Decimal(numbers) * 1000000)
    elif "B" in text:
        return int(Decimal(numbers) * 1000000000)
    else:
        return int(Decimal(numbers))


def num_to_text(num):
    num = float("{:.3g}".format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "{}{}".format(
        "{:f}".format(num).rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude]
    )


def commas(number):
    return "{:,}".format(number)


async def tornget(ctx, logger, endpoint, key, session=None, cache=30, nocache=False):
    url = f"https://api.torn.com/{endpoint}&key={key}&comment=Tornium"

    if key is None or key == "":
        embed = discord.Embed()
        embed.title = "Missing API Key"
        embed.description = "No API key was passed to the API call."
        await ctx.send(embed=embed)
        logger.error("No API key passed.")
        raise MissingKeyError

    redis = get_redis()

    if redis.exists(f"tornium:torn-cache:{url}") and not nocache:
        return redis.json().get(f"tornium:torn-cache:{url}")

    redis_key = f"tornium:torn-ratelimit:{key}"

    if redis.setnx(redis_key, 100):
        redis.expire(redis_key, 60 - datetime.datetime.utcnow().second)
    if redis.ttl(redis_key) < 0:
        redis.expire(redis_key, 1)
        redis.set(redis_key, 100)
        redis.expire(redis_key, 60 - datetime.datetime.utcnow().second)

    try:
        if redis.get(redis_key) is not None and int(redis.get(redis_key)) > 0:
            redis.decrby(redis_key, 1)
        else:
            if redis.get(redis_key) is None:
                redis.set(redis_key, 100)
                redis.expire(redis_key, 60 - datetime.datetime.utcnow().second)
            else:
                raise RatelimitError
    except TypeError as e:
        logger.warning(
            f"Error raised on API key {key} with redis return value {redis.get(redis_key)} and redis key {redis_key}"
        )

    if session is None:
        request = requests.get(url)
    else:
        request = session.get(url)

    if request.status_code != 200:
        embed = discord.Embed()
        embed.title = "Error"
        embed.description = (
            f"Something has possibly gone wrong with the request to the Torn API with "
            f"HTTP status code {request.status_code} has been given at "
            f"{datetime.datetime.now()}."
        )
        await ctx.send(embed=embed)
        logger.error(
            f"The Torn API has responded with HTTP status code {request.status_code}."
        )
        return NetworkingError(code=request.status_code, url=url)

    request = request.json()

    if "error" in request:
        error = request["error"]
        embed = discord.Embed()
        embed.title = "Error"
        embed.description = (
            f"Something has gone wrong with the request to the Torn API with error code "
            f"{error['code']} ({error['error']}). Visit the [Torn API documentation]"
            f"(https://api.torn.com/) to see why the error was raised."
        )
        await ctx.send(embed=embed)
        logger.error(f'The Torn API has responded with error code {error["code"]}.')
        raise TornError(code=request["error"]["code"], endpoint=url)

    if cache <= 0 or cache >= 60:
        return request
    elif sys.getsizeof(request) >= 500000:  # Half a megabyte
        return request

    redis.json().set(f"tornium:torn-cache:{url}", Path.root_path(), request)
    redis.expire(f"tornium:torn-cache:{url}", cache)

    return request
