# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from contextlib import nullcontext
import pickle

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
        (UnpickleableException(1, 2), pytest.raises(TypeError))
    ]
)
def test_celery_pickle(exception, expectation):
    with expectation:
        pickle.loads(pickle.dumps(exception))