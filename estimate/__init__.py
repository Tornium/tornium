# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import pathlib
import time
import typing

import pandas as pd
import xgboost
from peewee import JOIN, DoesNotExist
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.models import PersonalStats, User

_model: typing.Optional[xgboost.XGBRegressor] = None
model_features: typing.List[str] = None


def model() -> xgboost.XGBRegressor:
    global _model, model_features

    if _model is not None:
        return _model

    _model = xgboost.XGBRegressor()

    if pathlib.Path("estimate/models/base-model.json").exists():
        _model.load_model("estimate/models/base-model.json")
    else:
        _model.load_model("estimate/models/base-model-0.0.1.json")

    model_features = list(_model.feature_names_in_)

    return _model


def estimate_user(user_tid: int, api_key: str, allow_api_calls: bool = True) -> typing.Tuple[int, int]:
    if model() is None:
        raise ValueError("No model was loaded")

    redis_client = rds()
    allow_api_calls = False if api_key in (None, "") else allow_api_calls

    try:
        return int(redis_client.get(f"tornium:estimate:cache:{user_tid}")), int(time.time()) + redis_client.ttl(
            f"tornium:estimate:cache:{user_tid}"
        )
    except (ValueError, TypeError):
        pass

    ps: typing.Optional[PersonalStats]
    try:
        ps = User.select(User.personal_stats).join(PersonalStats).where(User.tid == user_tid).get().personal_stats
    except DoesNotExist:
        ps = None

    df: pd.DataFrame

    if ps is not None and int(time.time()) - ps.timestamp.timestamp() <= 604_800:  # One week
        df = pd.DataFrame(columns=model_features, index=[0])

        for field_name in model_features:
            df[field_name][0] = ps.__getattribute__(field_name)

        df["tid"][0] = user_tid
        df = df.astype("int64")

        estimate = int(model().predict(df))
        redis_client.set(f"tornium:estimate:cache:{user_tid}", estimate, ex=604_800)

        return estimate, int(time.time()) - ps.timestamp.timestamp() + 604_800

    if not allow_api_calls:
        raise PermissionError

    try:
        update_user(tid=user_tid, key=api_key, refresh_existing=True)
        update_error = False
    except Exception:
        update_error = True

    try:
        ps = User.select(User.personal_stats).join(PersonalStats).where(User.tid == user_tid).get().personal_stats
    except DoesNotExist:
        raise ValueError("Personal stats could not be found in the database")

    if not update_error and int(time.time()) - ps.timestamp.timestamp() > 604_800:  # One week
        raise ValueError("Personal stats data is too old after an update")

    df = pd.DataFrame(columns=model_features, index=[0])

    for field_name in model_features:
        df[field_name][0] = ps.__getattribute__(field_name)

    df["tid"][0] = user_tid
    df = df.astype("int64")

    estimate = int(model().predict(df))
    redis_client.set(f"tornium:estimate:cache:{user_tid}", estimate, ex=604_800)

    return estimate, int(time.time()) - ps.timestamp.timestamp() + 604_800
