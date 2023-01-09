# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import DynamicDocument, IntField, ListField, StringField


class KeyModel(DynamicDocument):
    key = StringField(primary_key=True)
    ownertid = IntField(default=0)
    scopes = ListField(default=[])  # List of scopes
