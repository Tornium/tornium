# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import BooleanField, DynamicDocument, FloatField, IntField, StringField, UUIDField


class UserModel(DynamicDocument):
    meta = {"indexes": ["#discord_id", ("+factionaa", "factionid"), "#key", "factionid"]}

    tid = IntField(primary_key=True)
    name = StringField(default="")
    level = IntField(default=0)
    last_refresh = IntField(default=0)
    admin = BooleanField(default=False)
    key = StringField(default="")
    battlescore = FloatField(default=0.0)
    battlescore_update = IntField(default=0)
    strength = FloatField(default=0.0)
    defense = FloatField(default=0.0)
    speed = FloatField(default=0.0)
    dexterity = FloatField(default=0.0)

    discord_id = IntField(default=0)

    factionid = IntField(default=0)
    factionaa = BooleanField(default=False)
    faction_position = UUIDField()  # UUID of Position in PositionModel
    chain_hits = IntField(default=0)

    status = StringField(default="")
    last_action = IntField(default=0)
