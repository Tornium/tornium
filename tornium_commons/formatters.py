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
import typing
from decimal import Decimal

from boltons.timeutils import relative_time


def get_tid(name: str) -> int:
    """
    Extracts the Torn ID from a passed Torn username.

    Parameters
    ----------
    name : str
        Torn username and ID

    Returns
    -------
    tid : int
        Torn ID

    Examples
    --------
    >>> get_tid(\"tiksan [2383326]\")
    2383326
    >>> get_tid("[2383326]")
    2383326
    """

    try:
        return int(re.compile(r"\[(\d+)\]").findall(name)[0])
    except IndexError:
        try:
            return int(name)
        except ValueError:
            return 0


def rel_time(ts: typing.Union[datetime.datetime, int, float]) -> str:
    """
    Convert Unix timestamp to a relative timestamp string.

    Parameters
    ----------
    ts : datetime.datetime, int, float
        Unix timestamp

    Returns
    -------
    relative_str : str
        Relative timestamp string
    """

    if type(ts) == int:
        datetime_obj = datetime.datetime.fromtimestamp(ts)
    elif type(ts) == float:
        datetime_obj = datetime.datetime.fromtimestamp(math.floor(ts))
    elif type(ts) == datetime.datetime:
        datetime_obj = ts
    else:
        raise AttributeError

    return relative_time(datetime_obj)


def commas(number: typing.Union[int, float], stock_price: bool = False) -> str:
    """
    Returns a string of the number with commas as the thousands separator.

    Parameters
    ----------
    number : int, float
        Number to be modified
    stock_price: bool, default: False
        Flag to determine if the number passed should be handled as a stock price

    Returns
    -------
    value : str
        String of number with commas as the thousands separator

    References
    ----------
    https://docs.python.org/3/library/string.html#format-specification-mini-language
    """

    if stock_price:
        return "{:,.2f}".format(number)
    return "{:,}".format(number)


def find_list(lst: list, key, value) -> typing.Union[int, list]:
    """
    Locate a dictionary in a list of dictionaries by a value in the dictionary.

    Utilized by Discord commands to determine the values of possible passed parameters.

    If the value is not found, -1 will be returned. Otherwise, a list of the index and dictionary will be returned.

    Parameters
    ----------
    lst : list
        The inputted list of dictionaries (options from the interaction)
    key :
        Key in the dictionary
    value :
        Value to be matched to the dictionary's value

    Returns
    -------
    value : int, list
        -1 if not found or [index, dictionary] if found

    Examples
    --------
    If the key and value are found,
    >>> find_list(interaction["data"]["options"], "tid", 2383326)
    [0, {...}]

    Otherwise,
    >>> find_list(interaction["data"]["options"], "tid", 2383326)
    -1
    """

    for i, dic in enumerate(lst):
        if dic.get(key) == value:
            return [i, dic]
    return -1


def text_to_num(text: str) -> int:
    """
    Convert a string of a number with a suffix to an integer.

    1K = 1,000
    1M = 1,000,000
    1B = 1,000,000,000

    Parameters
    ----------
    text : str
        String of a number with a suffix

    Returns
    -------
    number : int
        Integer of the number's string
    """

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


def bs_to_range(battlescore: typing.Union[int, float]) -> tuple:
    """
    Convert a stat score to a likely range of the total battle stats for the stat score.

    Parameters
    ----------
    battlescore : int, float
        Stat score

    Returns
    -------
    stat_range : tuple of int
        Tuple of the likely range of the total battle stats
    """

    return math.floor(pow(battlescore, 2) / 4), math.floor(pow(battlescore, 2) / 2.75)


def torn_timestamp(timestamp: typing.Optional[int, float] = None) -> str:
    """
    Return a formatted timestamp string of the passed timestamp or current time in the UTC timezone.

    Parameters
    ----------
    timestamp : int, float, optional
        Unix timestamp

    Returns
    -------
    time_string : str
        Formatted timestamp string
    """

    if timestamp is None:
        return datetime.datetime.utcnow().strftime("%m/%d %H:%M:%S TCT")
    else:
        return datetime.datetime.fromtimestamp(timestamp).strftime("%m/%d %H:%M:%S TCT")


def remove_html(text: str) -> str:
    """
    Remove HTML tags from string.

    Parameters
    ----------
    text : str
        String that may include HTML tags

    Returns
    -------
    text : str
        String without any HTML tags
    """

    cleaner = re.compile("<.*?>")
    return re.sub(cleaner, "", text)


def str_matches(input_str: str, items: typing.Union[list, set], starts: bool = False) -> list:
    """
    Returns list of which of the items match or start with the inputted string.

    Parameters
    ----------
    input_str : str
        String to be checked against
    items : list, set
        List of strings to be checked
    starts : bool, default: False

    Returns
    -------
    item_matches : list of bool
        List of booleans determining if item fulfilled the requirements
    """

    if starts:
        return [item for item in items if input_str.startswith(item)]
    else:
        return [item for item in items if item in input_str]
