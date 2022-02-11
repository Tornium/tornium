# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DynamicDocument, UUIDField, IntField


class RecruitModel(DynamicDocument):
    uuid = UUIDField(primary_key=True)
    tid = IntField()
    factionid = IntField()
    recruiter = IntField()
    messages_received = IntField()
    tif = IntField()
    status = IntField()

    # 0: Not Invited
    # 1: Invited
    # 2: Joined
