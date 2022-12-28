# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
from decimal import Decimal
import logging
import re
from typing import Union
from urllib.parse import urlparse

from flask import render_template

from utils.errors import DiscordError, MissingKeyError, NetworkingError, TornError


def get_logger():
    return logging.getLogger("server")


def get_tid(name):
    try:
        return int(re.compile(r"\[(\d+)\]").findall(name)[0])
    except IndexError:
        try:
            return int(name)
        except ValueError:
            return 0


def get_torn_name(name):
    return re.sub("[[].*?[]]", "", name).replace(" ", "")


def handle_torn_error(error: TornError):
    if error.code == 0:
        return render_template(
            "/errors/error.html",
            title="Unknown Error",
            error="The Torn API has returned an unknown error.",
        )
    elif error.code == 1:
        return render_template(
            "/errors/error.html",
            title="Empty Key",
            error="The passed Torn API key was empty (i.e. no Torn API key was passed).",
        )
    elif error.code == 2:
        return render_template(
            "/errors/error.html",
            title="Incorrect Key",
            error="The passed Torn API key was not a valid key.",
        )
    elif error.code == 5:
        return render_template(
            "/errors/error.html",
            title="Too Many Requests",
            error="The passed Torn API key has had more than 100 requests sent to the Torn "
            "API server. Please try again in a couple minutes.",
        )
    elif error.code == 8:
        return render_template(
            "/errors/error.html",
            title="IP Block",
            error="The server on which this site is hosted has made more than 2000 API calls "
            "this minute has has been temporarily banned by Torn's servers for a minute. "
            "Please contact the administrators of this site to inform them of this so "
            "that changes can be made.",
        )
    elif error.code == 9:
        return render_template(
            "/errors/error.html",
            title="API System Disabled",
            error="Torn's API system has been temporarily disabled. Please try again in a " "couple minutes.",
        )
    elif error.code == 10:
        return render_template(
            "/errors/error.html",
            title="Key Owner Fedded",
            error="The owner of the passed API key has been fedded. Please verify that the "
            "inputted API key is correct.",
        )
    elif error.code == 11:
        return render_template(
            "/errors/error.html",
            title="Key Change Error",
            error="You can only change your API key once every 60 seconds.",
        )
    elif error.code == 13:
        return render_template(
            "/errors/error.html",
            title="Key Change Error",
            error="The owner of the passed API key has not been online for more than 7 days. "
            "Please verify that the inputted API key is correct.",
        )
    elif error.code == 17:
        return render_template(
            "/errors/error.html",
            title="Internal Torn API Error",
            error="An internal backend error has occurred with the Torn API. Please try again.",
        )
    else:
        return render_template(
            "/errors/error.html",
            title="Miscellaneous Error",
            error=f"The Torn API has responded with error code {error.code}",
        )


def handle_discord_error(error: DiscordError):
    if error.code == 0:
        return render_template(
            "/errors/error.html",
            title="General Error",
            error="The Discord API has returned a general error.",
        )
    elif error.code == 10003:
        return render_template(
            "/errors/error.html",
            title="Unknown Channel",
            error="The passed guild channel could not be found.",
        )
    elif error.code == 10004:
        return render_template(
            "/errors/error.html",
            title="Unknown Guild",
            error="The passed guild could not be found.",
        )
    elif error.code == 10007:
        return render_template(
            "/errors/error.html",
            title="Unknown Member",
            error="The passed guild member could not be found.",
        )
    elif error.code == 10008:
        return render_template(
            "/errors/error.html",
            title="Unknown Message",
            error="The passed message could not be found.",
        )
    elif error.code == 10011:
        return render_template(
            "/errors/error.html",
            title="Unknown Role",
            error="The passed guild role could not be found.",
        )
    elif error.code == 10012:
        return render_template(
            "/errors/error.html",
            title="Unknown Token",
            error="The passed bot token is not correct. Please immediately contact the bot/app "
            "hoster in order for the bot token to be replaced.",
        )
    elif error.code == 10013:
        return render_template(
            "/errors/error.html",
            title="Unknown User",
            error="The passed Discord user could not be found.",
        )
    elif error.code == 40001:
        return render_template(
            "/errors/error.html",
            title="Unauthorized",
            error="The passed bot token is not valid. Please immediately contact the bot/app "
            "hoster in order for the bot token to be replaced.",
        )
    else:
        return render_template(
            "/errors/error.html",
            title="Miscellaneous Error",
            error=f"The Discord API has responded with error code {error.code} that is not currently in "
            f"the handled list of Discord API errors. Please report this error.code to the "
            f"developer(s). A full list of Discord API errors can be found at "
            f"https://discord.com/developers/docs/topics/opcodes-and-status-codes#json",
        )


def handle_networking_error(error: NetworkingError):
    if error.code == 408 and urlparse(error.url).hostname == "www.torn.com":
        return render_template(
            "/errors/error.html",
            title="Torn API Timed Out",
            error="The Torn API did not respond within the prescribed time period. Please try again. This issue "
            "originates from Torn's servers.",
        )

    return render_template(
        "/errors/error.html",
        title="Miscellaneous Error",
        error=f"An API has responded with HTTP {error.code}.",
    )


def now():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())


def remove_str(text):
    return int("".join(filter(lambda x: x.isdigit(), text)))


def rel_time(time: Union[datetime.datetime, int, float]):
    if type(time) == datetime.datetime:
        delta = now() - int(time.timestamp())
    elif type(time) in (int, float):
        delta = now() - time
    else:
        raise AttributeError

    if delta < 60:  # One minute
        return "Now"
    elif delta < 3600:  # Sixty minutes
        if int(round(delta / 60)) == 1:
            return f"{int(round(delta/60))} minute ago"
        else:
            return f"{int(round(delta/60))} minutes ago"
    elif delta < 86400:  # One day
        if int(round(delta / 3600)) == 1:
            return f"{int(round(delta/3600))} hours ago"
        else:
            return f"{int(round(delta/3600))} hours ago"
    elif delta < 2592000:  # Thirty days
        if int(round(delta / 86400)) == 1:
            return f"{int(round(delta/86400))} day ago"
        else:
            return f"{int(round(delta/86400))} days ago"
    elif delta < 31104000:  # Twelve months
        if int(round(delta / 2592000)) == 1:
            return f"{int(round(delta/2592000))} month ago"
        else:
            return f"{int(round(delta/2592000))} months ago"
    else:
        return "A long time ago"


def torn_timestamp(timestamp=None):
    if timestamp is None:
        return datetime.datetime.utcnow().strftime("%m/%d %H:%M:%S TCT")
    else:
        return datetime.datetime.fromtimestamp(timestamp).strftime("%m/%d %H:%M:%S TCT")


def remove_html(text):
    cleaner = re.compile("<.*?>")
    return re.sub(cleaner, "", text)


def first(array):
    return None if len(array) == 0 else array[0]


def commas(number):
    return "{:,}".format(number)


def find_list(lst: list, key, value):
    """
    Find a dictionary in a list of dictionaries by a value in the dictionary
    """

    for i, dic in enumerate(lst):
        if dic[key] == value:
            return [i, dic]
    return -1


def text_to_num(text):
    text = text.upper().replace(",", "")
    numbers = re.sub("[a-z]", "", text.lower())

    if "K" in text:
        return int(Decimal(numbers) * 1000)
    elif "M" in text:
        return int(Decimal(numbers) * 1000000)
    elif "B" in text:
        return int(Decimal(numbers) * 1000000000)
    else:
        return int(Decimal(numbers))
