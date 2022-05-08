# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DynamicDocument, IntField, UUIDField, StringField, DictField


class ScheduleModel(DynamicDocument):
    uuid = UUIDField(primary_key=True)
    factiontid = IntField(default=0)
    name = StringField(default="")
    timecreated = IntField(default=0)
    timeupdated = IntField(default=0)
    activity = DictField(default={})
    weight = DictField(default={})
    schedule = DictField(default={})
    fromts = IntField(default=0)
    tots = IntField(default=0)
