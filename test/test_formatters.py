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

import locale
import string

import hypothesis
import pytest
from hypothesis import strategies as st

from tornium_commons.formatters import commas, get_tid, text_to_num


@hypothesis.given(st.text(alphabet=string.printable))
@hypothesis.example("Chedburn [1]")
@hypothesis.example("Chedburn")
@hypothesis.example("1")
@hypothesis.example("[1]")
@hypothesis.example(" [1]")
@hypothesis.example("[]")
@hypothesis.example(" []")
def test_get_tid(name: str):
    for i in range(len(name)):
        if name[i] != "[":
            continue

        for j in reversed(range(i, len(name))):
            if name[j] != "]":
                continue

            if name[i + 1 : j].isdigit():
                r = int(name[i + 1 : j])
                break
        else:
            continue

        break
    else:
        r = 0

    assert get_tid(name) == r, f'Failed to match the Torn ID of "{name}"'


@hypothesis.given(st.integers(min_value=0))
def test_commas_int(n):
    locale.setlocale(locale.LC_ALL, "en_US.utf8")
    assert commas(n, stock_price=False) == locale.format_string("%d", n, grouping=True), f"Failed to format {n}"
    assert commas(n, stock_price=True) == locale.currency(n, grouping=True)[1:], f"Failed to format {n} as currency"


@hypothesis.given(st.floats(min_value=0))
def test_commas_floats(n):
    locale.setlocale(locale.LC_ALL, "en_US.utf8")
    assert commas(n, stock_price=True) == locale.currency(n, grouping=True)[1:], f"Failed to format {n} as currency"


@pytest.mark.parametrize(
    "s,n",
    [
        ("0", 0),
        (12, AttributeError),
        (12.0, AttributeError),
        ("1k", 1_000),
        ("1K", 1_000),
        ("1.32K", 1_320),
        ("1.3284K", 1_328.4),
        ("-1.2K", -1_200),
        ("12M", 12_000_000),
        ("2311M", 2_311_000_000),
        ("23.3B", 23_300_000_000),
        ("6927B", 6_927_000_000_000),
        ("372H", ValueError),
    ],
)
def test_text_to_num(s, n):
    if type(n) == type and isinstance(n(), Exception):
        with pytest.raises(n):
            text_to_num(s)
    else:
        assert text_to_num(s) == n, f"Failed to parse {s}"
