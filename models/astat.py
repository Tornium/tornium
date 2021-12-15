# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster.deeksh@gmail.com>

from mongoengine import DynamicDocument, IntField, ListField, FloatField


class AStatModel(DynamicDocument):
    sid = IntField(primary_key=True)
    tid = IntField()
    timeadded = IntField()
    addedid = IntField()
    factiontid = IntField()
    str0 = FloatField(default=0)
    str1 = FloatField(default=0)
    def0 = FloatField(default=0)
    def1 = FloatField(default=0)
    spd0 = FloatField(default=0)
    spd1 = FloatField(default=0)
    dex0 = FloatField(default=0)
    dex1 = FloatField(default=0)
    battlescore0 = FloatField(default=0)
    battlescore1 = FloatField(default=0)
    attacks = ListField(default=[])
