# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from skynet.commands.stocks import notify

_stocks_commands = {"notify": notify.notify}


def stocks_switchboard(interaction):
    if interaction["data"]["options"][0]["name"] in _stocks_commands:
        return _stocks_commands[interaction["data"]["options"][0]["name"]](interaction)

    return {}
