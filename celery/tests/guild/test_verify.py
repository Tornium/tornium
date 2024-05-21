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

import string

import hypothesis
from tornium_commons.models import FactionPosition

from tornium_celery.tasks.guild import (
    member_faction_roles,
    member_position_roles,
    member_verification_name,
    member_verified_roles,
)


@hypothesis.given(hypothesis.strategies.integers(min_value=1), hypothesis.strategies.text(alphabet=string.printable))
def test_default_verification_name(tid: int, name: str):
    assert member_verification_name(name=name, tid=tid, tag="")


def test_empty_verified_roles():
    assert member_verified_roles([]) == set()


def test_small_verified_roles():
    assert member_verified_roles([1, 2, 3]) == {"1", "2", "3"}


def test_empty_faction_roles():
    assert (
        member_faction_roles(faction_verify={"1": {"roles": [], "positions": {}, "enabled": True}}, faction_id=0)
        == set()
    )
    assert (
        member_faction_roles(faction_verify={"1": {"roles": [], "positions": {}, "enabled": True}}, faction_id=3)
        == set()
    )
    assert (
        member_faction_roles(faction_verify={"1": {"roles": [], "positions": {}, "enabled": True}}, faction_id=1)
        == set()
    )
    assert (
        member_faction_roles(faction_verify={"1": {"roles": [], "positions": {}, "enabled": False}}, faction_id=1)
        == set()
    )
    assert (
        member_faction_roles(
            faction_verify={"1": {"roles": [1, 2, 3], "positions": {}, "enabled": False}}, faction_id=1
        )
        == set()
    )


def test_valid_faction_roles():
    assert member_faction_roles(
        faction_verify={"1": {"roles": [1, 2, 3], "positions": {}, "enabled": True}}, faction_id=1
    ) == {"1", "2", "3"}


def test_empty_position_roles():
    assert (
        member_position_roles(
            faction_verify={"1": {"roles": [], "positions": {"abc": [1, 2, 3], "123": []}, "enabled": False}},
            faction_id=0,
            position=FactionPosition(pid="abc", name="abc"),
        )
        == set()
    )
    assert (
        member_position_roles(
            faction_verify={"1": {"roles": [], "positions": {"abc": [1, 2, 3], "123": []}, "enabled": True}},
            faction_id=0,
            position=FactionPosition(pid="abc", name="abc"),
        )
        == set()
    )
    assert (
        member_position_roles(
            faction_verify={"1": {"roles": [], "positions": {"abc": [1, 2, 3], "123": []}, "enabled": False}},
            faction_id=1,
            position=FactionPosition(pid="abc", name="abc"),
        )
        == set()
    )
    assert (
        member_position_roles(
            faction_verify={"1": {"roles": [], "positions": {"abc": [1, 2, 3], "123": []}, "enabled": True}},
            faction_id=1,
            position=FactionPosition(pid="123", name="abc"),
        )
        == set()
    )
