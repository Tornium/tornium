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

import pickle
from contextlib import nullcontext

import pytest

import utils.errors


class UnpickleableException(Exception):
    def __init__(self, a, b):
        super().__init__()

        self.a = a
        self.b = b


@pytest.mark.parametrize(
    "exception,expectation",
    [
        (utils.errors.NetworkingError(400, "https://www.example.com"), nullcontext()),
        (utils.errors.NetworkingError(200, "https://www.example.com"), nullcontext()),
        (utils.errors.TornError(5, "https://www.example.com"), nullcontext()),
        (utils.errors.TornError(7, "https://www.example.com"), nullcontext()),
        (utils.errors.DiscordError(10001, "Unknown Account"), nullcontext()),
        (utils.errors.DiscordError(10004, "Unknown Guild"), nullcontext()),
        (utils.errors.DiscordError(1, "test"), nullcontext()),
        (utils.errors.MissingKeyError(), nullcontext()),
        (utils.errors.RatelimitError(), nullcontext()),
        (UnpickleableException(1, 2), pytest.raises(TypeError)),
    ],
)
def test_celery_pickle(exception, expectation):
    with expectation:
        pickle.loads(pickle.dumps(exception))
