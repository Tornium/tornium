# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DynamicDocument, IntField, BooleanField, ListField


class StatModel(DynamicDocument):
    statid = IntField(primary_key=True)
    tid = IntField(default=0)
    battlescore = IntField(default=0)
    timeadded = IntField(default=0)
    addedid = IntField(default=0)
    addedfactiontid = IntField(default=0)
    globalstat = BooleanField(default=False)
    allowedfactions = ListField()
