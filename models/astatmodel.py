# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import (
    DynamicDocument,
    IntField,
    ListField,
    StringField,
    FloatField,
    BooleanField,
)


class AStatModel(DynamicDocument):
    sid = IntField(primary_key=True)
    logid = StringField()
    tid = IntField()
    timeadded = IntField()
    addedid = IntField()
    addedfactiontid = IntField()
    status = StringField(default="notStarted")
    dbs = ListField(default=[])
    attackerstr = FloatField()
    attackerdef = FloatField()
    attackerspd = FloatField()
    attackerdex = FloatField()
    globalstat = BooleanField(default=False)
    allowedfactions = ListField()
