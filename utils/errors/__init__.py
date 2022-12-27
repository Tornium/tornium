# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from utils.errors.discord import DiscordError
from utils.errors.networking import NetworkingError
from utils.errors.torn import MissingKeyError, TornError


class RatelimitError(Exception):
    pass
