# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>


from mongoengine import DynamicDocument, IntField, StringField, ListField


class FactionGroupModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField()
    creator = IntField()
    members = ListField()
    invite = StringField()

    sharestats = ListField(default=[])
