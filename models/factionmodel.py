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
)


class FactionModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField(default="")
    respect = IntField(default=0)
    capacity = IntField(default=0)
    leader = IntField(default=0)
    coleader = IntField(default=0)
    aa_keys = ListField(default=[])

    last_members = IntField(default=0)  # Time of last members update
    last_attacks = IntField(default=0)

    guild = IntField(default=0)  # Guild ID of the faction's guild
    config = DictField(default={"vault": 0, "stats": 1})  # Dictionary of faction's bot configuration
    vaultconfig = DictField(default={"banking": 0, "banker": 0})  # Dictionary of vault configuration

    statconfig = DictField(default={"global": 0})  # Dictionary of target config

    chainconfig = DictField(default={"od": 0, "odchannel": 0})  # Dictionary of chain config
    chainod = DictField(default={})  # Dictionary of faction member overdoses
