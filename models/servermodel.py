# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import (
    DynamicDocument,
    IntField,
    StringField,
    DictField,
    ListField,
    LongField,
    BooleanField,
)


class ServerModel(DynamicDocument):
    sid = LongField(primary_key=True)
    name = StringField(default="")
    admins = ListField(default=[])  # List of admin ids
    prefix = StringField(default="?")
    config = DictField(
        default={"stakeouts": 0, "assists": 0}
    )  # Dictionary of server configurations

    factions = ListField(default=[])  # List of factions in server

    stakeoutconfig = DictField(
        default={"category": 0}
    )  # Dictionary of stakeout configurations for the server
    userstakeouts = ListField(default=[])  # List of staked-out users
    factionstakeouts = ListField(default=[])  # List of staked-out factions

    assistschannel = IntField(default=0)
    assist_factions = ListField(
        default=[]
    )  # List of factions that can send assists to the server
    assist_mod = IntField(default=0)  # 0: Everyone; 1: Whitelist; 2: Blacklist

    skynet = BooleanField(default=False)
