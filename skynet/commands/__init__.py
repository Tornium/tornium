# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from skynet.commands import faction, user, bot, stat
from skynet.skyutils import SKYNET_INFO


def ping(interaction):
    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Pong",
                    "image": {"url": "https://media3.giphy.com/media/pWncxUrrNHdny/giphy.gif"},
                    "color": SKYNET_INFO,
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }
