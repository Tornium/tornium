# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DynamicDocument, IntField, BooleanField, DynamicField, DictField


class NotificationModel(DynamicDocument):
    #### ntype ####
    # Notification types
    #
    # 0: stocks price reach
    ###############

    invoker = IntField(required=True)  # TID of notification creator
    time_created = IntField(required=True)

    recipient = IntField(required=True)
    recipient_type = IntField(required=True)  # 0: DM; 1: channel

    ntype = IntField(required=True)
    target = DynamicField(required=True)
    persistent = BooleanField(default=False)
    value = DynamicField()
    options = DictField(default={})
