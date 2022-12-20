# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import random
import time

from mongoengine.queryset.visitor import Q

from models.tickmodel import TickModel
from models.usermodel import UserModel
from tasks import celery_app, logger, tornget
import utils


@celery_app.task
def fetch_stock_ticks():
    time.sleep(5)  # Torn has stock tick data ready at xx:xx:05

    auth_users = [user.key for user in UserModel.objects(Q(key__exists=True) & Q(key__ne=""))]
    random.shuffle(auth_users)

    stocks_data = None
    torn_key = random.choice(auth_users)
    timeout_retry = False

    while stocks_data is None:
        try:
            stocks_data = tornget(
                "torn/?selections=stocks", key=torn_key, nocache=True
            )
        except utils.TornError as e:
            if e.code in (1, 2, 3, 4, 6, 7, 8, 9):
                return

            torn_key = random.choice(auth_users)
        except utils.NetworkingError as e:
            if e.code == 408 and not timeout_retry:
                timeout_retry = True
                continue

            torn_key = random.choice(auth_users)
            timeout_retry = False

    if stocks_data is None:
        return

    tick_data = []
    now = datetime.datetime.utcnow()
    now = int(datetime.datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        second=0,
    ).replace(tzinfo=datetime.timezone.utc).timestamp())
    binary_timestamp = bin(now << 8)

    for stock in stocks_data["stocks"].values():
        binary_stockid = bin(stock["stock_id"])

        tick_data.append({
            "tick_id": int(binary_stockid, 2) + int(binary_timestamp, 2),
            "timestamp": now,
            "stock_id": stock["stock_id"],
            "price": stock["current_price"],
            "cap": stock["market_cap"],
            "shares": stock["total_shares"],
            "investors": stock["investors"],
        })

    tick_data = [TickModel(**tick) for tick in tick_data]
    TickModel.objects.insert(tick_data)
