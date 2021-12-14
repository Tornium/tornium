# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster.deeksh@gmail.com>

from mongoengine import DynamicDocument, IntField, StringField, ListField, BooleanField, FloatField


class UserModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField(default='')
    level = IntField(default=0)
    last_refresh = IntField(default=0)
    admin = BooleanField(default=False)
    key = StringField(default='')
    battlescore = FloatField(default=0.0)
    battlescore_update = IntField(default=0)

    discord_id = IntField(default=0)
    servers = ListField(default=[])  # List of discord servers where user is admin

    factionid = IntField(default=0)
    factionaa = BooleanField(default=False)
    chain_hits = IntField(default=0)

    status = StringField(default='')
    last_action = IntField(default=0)

    pro = BooleanField(default=False)
    pro_expiration = IntField(default=0)
