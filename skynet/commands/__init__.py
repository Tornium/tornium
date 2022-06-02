# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from skynet.commands import faction


def ping(interaction):
    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Pong",
                    "image": {
                        "url": "https://media3.giphy.com/media/pWncxUrrNHdny/giphy.gif"
                    },
                    "color": 0x7DF9FF,
                }
            ],
            "flags": 64  # Ephemeral
        },
    }


def sr(interaction):
    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "SR",
                    "video": {
                        "url": "https://www.youtube.com/embed/LDU_Txk06tM"
                    },
                    "color": 0x7DF9FF
                }
                
            ]
        }
    }
