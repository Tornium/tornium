# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DictField, DynamicDocument, IntField


class FactionStakeoutModel(DynamicDocument):
    tid = IntField(primary_key=True)  # The faction ID of the stakeout
    data = DictField(default={})  # Faction data from the Torn API
    guilds = DictField(default={})  # Dictionary of guilds and keys to be watched
    last_update = IntField(default=0)
