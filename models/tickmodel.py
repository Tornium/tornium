# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from mongoengine import Document, IntField, FloatField, LongField


class TickModel(Document):
    tick_id = IntField(primary_key=True)
    timestamp = IntField()
    stock_id = IntField()
    price = FloatField()
    cap = LongField()
    shares = LongField()
    investors = IntField()
