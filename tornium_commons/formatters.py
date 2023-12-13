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

import dataclasses
import datetime
import math
import re
import typing
from decimal import Decimal

from boltons.timeutils import relative_time
from peewee import DoesNotExist

from .models import Item


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

    if isinstance(ts, int):
        datetime_obj = datetime.datetime.fromtimestamp(ts)
    elif isinstance(ts, float):
        datetime_obj = datetime.datetime.fromtimestamp(math.floor(ts))
    elif isinstance(ts, datetime.datetime):
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


def find_list(lst: list, key, value) -> typing.Union[int, typing.List[typing.Union[int, typing.Dict[str, typing.Any]]]]:
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

    1  = 1
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

    Raises
    ------
    ValueError
        If there's an unknown suffix
    """

    text = text.strip("$").upper().replace(",", "")
    numbers = re.sub("[a-z]", "", text.lower())

    if text.isdigit():
        return int(text)
    elif text.endswith("K"):
        return int(Decimal(numbers) * 1000)
    elif text.endswith("M"):
        return int(Decimal(numbers) * 1000000)
    elif text.endswith("B"):
        return int(Decimal(numbers) * 1000000000)
    else:
        raise ValueError


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


def torn_timestamp(timestamp: typing.Optional[typing.Union[int, float, datetime.datetime]] = None) -> str:
    """
    Return a formatted timestamp string of the passed timestamp or current time in the UTC timezone.

    Parameters
    ----------
    timestamp : int, float, datetime.datetime, optional
        Unix timestamp

    Returns
    -------
    time_string : str
        Formatted timestamp string
    """

    if timestamp is None:
        timestamp = datetime.datetime.utcnow()
    elif not isinstance(timestamp, datetime.datetime):
        timestamp = datetime.datetime.fromtimestamp(timestamp)

    timestamp: datetime.datetime
    return timestamp.strftime("%m/%d %H:%M:%S TCT")


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


def parse_item_str(input_str: str) -> typing.Tuple[int, typing.Optional[Item]]:
    """
    Parse an item string into the item quantity and Item

    Parameters
    ----------
    input_str : str
        String to be parsed

    Returns
    -------
    quantity : int
        Number of items
    item : Item, optional
        Database entry of the item if one exists

    Examples
    --------
    >>> parse_item_str("3x Feathery Hotel Coupon")
    (3, Item(367))
    >>> parse_item_str("1x Random Property")
    (1, None)
    """

    input_str_split = input_str.split("x ")

    quantity: typing.Union[str, int] = input_str_split[0]
    item_str: str = "x ".join(input_str_split[1:])

    if quantity.isdigit():
        quantity = int(quantity)

        if quantity <= 0:
            raise ValueError("Illegal quantity")

    item: typing.Optional[Item]
    try:
        item = Item.get(Item.name == item_str)
    except DoesNotExist:
        item = None

    return quantity, item


def discord_escaper(value: str) -> str:
    return value.replace("*", "\\*").replace("_", "\\_")


@dataclasses.dataclass
class HumanTimeDelta:
    seconds: int = 0
    minutes: int = 0
    hours: int = 0
    days: int = 0
    weeks: int = 0
    months: int = 0
    years: int = 0

    def __setattr__(self, key, value):
        if not isinstance(value, int):
            raise TypeError(f"input type must be an integer, not {type(value)}")
        elif value < 0:
            raise ValueError("input must be greater than or equal to zero")

        minutes, seconds = divmod(value, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        years, days = divmod(days, 365)
        months, days = divmod(days, 30)
        weeks, days = divmod(days, 7)

        super().__setattr__("seconds", seconds)
        super().__setattr__("minutes", minutes)
        super().__setattr__("hours", hours)
        super().__setattr__("days", days)
        super().__setattr__("weeks", weeks)
        super().__setattr__("months", months)
        super().__setattr__("years", years)

    def __iter__(self):
        for key in self.__dict__.__reversed__():
            value = self.__dict__[key]

            if value == 0:
                continue
            elif value == 1:
                yield f"1 {key[:-1]}"
            else:
                yield f"{value} {key}"

        return self

    def __str__(self):
        return self.trunc(and_seperator=False)

    def __repr__(self):
        _s = [t_u for t_u in self]

        if len(_s) == 0:
            return ""
        elif len(_s) == 1:
            return _s[0]
        elif len(_s) == 2:
            return f"{_s[0]} and {_s[1]}"
        else:
            return ", ".join(_s[:-1]) + ", and " + _s[-1]

    def trunc(self, max_count: int = 2, seperator: str = ", ", and_seperator: bool = True):
        _c = 0
        _s = []

        time_unit: str
        for time_unit in self:
            _s.append(time_unit)
            _c += 1

            if _c >= max_count:
                break

        if len(_s) == 0:
            return ""
        elif len(_s) == 1:
            return _s[0]
        elif len(_s) == 2:
            if not and_seperator and seperator == "":
                return f"{_s[0]}, {_s[1]}"
            elif not and_seperator:
                return f"{_s[0]}{seperator}{_s[1]}"

            return f"{_s[0]} and {_s[1]}"
        else:
            if and_seperator:
                return f"{seperator.join(_s[:-1])}, and {_s[-1]}"
            else:
                return seperator.join(_s)
