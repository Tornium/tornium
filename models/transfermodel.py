# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DynamicDocument, IntField


class TransferModel(DynamicDocument):
    tid = IntField(primary_key=True)  # The transfer ID
    factiontid = IntField()
    amount = IntField()
    requester = IntField()
    recipient = IntField()
    time_requested = IntField()
    fulfiller = IntField()
    time_fulfilled = IntField()
    transfer_message = IntField()
    ttype = IntField(default=0)  # 0: cash; 1: points
