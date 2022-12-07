# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DynamicDocument, IntField, ListField, BooleanField


class OCModel(DynamicDocument):
    meta = {"indexes": ["factiontid", ("factiontid", "ocid")]}

    factiontid = IntField(required=True)
    ocid = IntField(required=True)
    crime_id = IntField(required=True)
    participants = ListField(required=True)
    time_started = IntField(required=True)
    time_ready = IntField(required=True)
    time_completed = IntField(required=True)  # 0 if not initiated yet
    planned_by = IntField(required=True)
    initiated_by = IntField(default=0)  # 0 if not initiated yet
    money_gain = IntField(default=0)  # 0 if not initiated yet
    respect_gain = IntField(default=0)  # 0 if not initiated yet
    delayers = ListField(default=[])
    notified = BooleanField(default=False)
