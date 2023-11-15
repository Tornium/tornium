# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import pathlib
import os
import time
import typing

import pandas as pd
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.models import PersonalStats, User
import xgboost


model: typing.Optional[xgboost.XGBRegressor] = None
model_features: typing.List[str] = None

if model is None:
    model = xgboost.XGBRegressor()

    if pathlib.Path("estimate/models/base-model.json").exists():
        model.load_model("estimate/models/base-model.json")
    else:
        model.load_model("estimate/models/base-model-0.0.1.json")

    model_features = list(model.feature_names_in_)


def estimate_user(user_tid: int, api_key: str) -> typing.Tuple[int, int]:
    if model is None:
        raise ValueError("No model was loaded")

    redis_client = rds()

    try:
        return int(redis_client.get(f"tornium:estimate:cache:{user_tid}")), int(time.time()) + redis_client.ttl(
            f"tornium:estimate:cache:{user_tid}"
        )
    except (ValueError, TypeError):
        pass

    ps: typing.Optional[PersonalStats] = (
        PersonalStats.select().where(PersonalStats.tid == user_tid).order_by(-PersonalStats.timestamp).first()
    )
    df: pd.DataFrame

    if ps is not None and int(time.time()) - ps.timestamp.timestamp() <= 604_800:  # One week
        df = pd.DataFrame(columns=model_features, index=[0])

        for field_name in model_features:
            df[field_name][0] = ps.__getattribute__(field_name)

        df["tid"][0] = user_tid
        df = df.astype("int64")

        return model.predict(df), int(time.time()) - ps.timestamp.timestamp() + 604_800

    try:
        update_user(tid=user_tid, key=api_key, refresh_existing=True)
        update_error = False
    except Exception:
        update_error = True

    ps = PersonalStats.select().where(PersonalStats.tid == user_tid).order_by(-PersonalStats.timestamp).first()

    if ps is None:
        raise ValueError("Personal stats could not be found in the database")
    elif not update_error and int(time.time()) - ps.timestamp.timestamp() > 604_800:  # One week
        raise ValueError("Personal stats data is too old after an update")

    df = pd.DataFrame(columns=model_features, index=[0])

    for field_name in model_features:
        df[field_name][0] = ps.__getattribute__(field_name)

    df["tid"][0] = user_tid
    df = df.astype("int64")

    return model.predict(df), int(time.time()) - ps.timestamp.timestamp() + 604_800
