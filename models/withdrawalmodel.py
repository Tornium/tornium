# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DynamicDocument, IntField


class WithdrawalModel(DynamicDocument):
    wid = IntField(primary_key=True)  # The withdrawal ID
    factiontid = IntField()
    amount = IntField()
    requester = IntField()
    time_requested = IntField()
    fulfiller = IntField()
    time_fulfilled = IntField()
    withdrawal_message = IntField()
