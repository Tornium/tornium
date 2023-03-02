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
import re
import time
import typing
from decimal import Decimal


def get_tid(name: str) -> int:
    try:
        return int(re.compile(r"\[(\d+)\]").findall(name)[0])
    except IndexError:
        try:
            return int(name)
        except ValueError:
            return 0


def get_torn_name(name: str) -> str:
    return re.sub("[[].*?[]]", "", name).replace(" ", "")


def remove_str(text: str) -> int:
    return int("".join(filter(lambda x: x.isdigit(), text)))


def rel_time(ts: typing.Union[datetime.datetime, int, float]) -> str:
    if type(ts) == datetime.datetime:
        delta = time.time() - int(ts.timestamp())
    elif type(ts) in (int, float):
        delta = time.time() - ts
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


def commas(number: int, stock_price: bool=False):
    if stock_price:
        return "{:,.2f}".format(number)
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


def bs_to_range(battlescore):
    return math.floor(pow(battlescore, 2) / 4), math.floor(pow(battlescore, 2) / 2.75)


def torn_timestamp(timestamp=None):
    if timestamp is None:
        return datetime.datetime.utcnow().strftime("%m/%d %H:%M:%S TCT")
    else:
        return datetime.datetime.fromtimestamp(timestamp).strftime("%m/%d %H:%M:%S TCT")


def remove_html(text):
    cleaner = re.compile("<.*?>")
    return re.sub(cleaner, "", text)
