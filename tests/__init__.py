# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>


def pytest_configure(config):
    # PyTest run detection: https://stackoverflow.com/a/25188424
    import sys
    sys._called_from_test = True


def pytest_unconfigure(config):
    import sys
    del sys._called_from_test
