# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import pathlib
import time
import typing

import pandas as pd
import xgboost
from peewee import DoesNotExist
from tornium_celery.tasks.user import update_user
from tornium_commons import rds
from tornium_commons.formatters import date_to_timestamp
from tornium_commons.models import PersonalStats, User

_model: typing.Optional[xgboost.XGBRegressor] = None
model_features: typing.List[str] = None

ESTIMATE_TTL = 604_800  # One week


def model() -> xgboost.XGBRegressor:
    global _model, model_features

    if _model is not None:
        return _model

    _model = xgboost.XGBRegressor()

    if pathlib.Path("estimate/models/base-model.json").exists():
        _model.load_model("estimate/models/base-model.json")
    else:
        _model.load_model("estimate/models/base-model-0.0.1.json")

    if model_features is None:
        model_features = list(_model.feature_names_in_)

    return _model


def estimate_user(user_tid: int, api_key: str, allow_api_calls: bool = True) -> typing.Tuple[int, int]:
    if model() is None:
        raise ValueError("No model was loaded")

    redis_client = rds()
    allow_api_calls = False if api_key in (None, "") else allow_api_calls
    now = int(time.time())

    try:
        return int(redis_client.get(f"tornium:estimate:cache:{user_tid}")), now + redis_client.ttl(
            f"tornium:estimate:cache:{user_tid}"
        )
    except (ValueError, TypeError):
        pass

    ps: typing.Optional[PersonalStats] = (
        PersonalStats.select().where(PersonalStats.user == user_tid).order_by(-PersonalStats.timestamp).first()
    )

    df: pd.DataFrame
    if ps is not None and now - date_to_timestamp(ps.timestamp) <= ESTIMATE_TTL:
        df = pd.DataFrame(columns=model_features, index=[0])

        for field_name in model_features:
            try:
                df[field_name][0] = ps.__getattribute__(field_name)
            except AttributeError:
                df[field_name][0] = 0

        df["tid"][0] = user_tid
        df = df.astype("int64")

        estimate = int(model().predict(df))
        redis_client.set(f"tornium:estimate:cache:{user_tid}", estimate, ex=ESTIMATE_TTL)

        return estimate, now - date_to_timestamp(ps.timestamp) + ESTIMATE_TTL

    if not allow_api_calls:
        raise PermissionError

    try:
        update_user(tid=user_tid, key=api_key, refresh_existing=True)
        update_error = False
    except Exception:
        update_error = True

    try:
        ps = PersonalStats.select().where(PersonalStats.user == user_tid).order_by(-PersonalStats.timestamp).get()
    except DoesNotExist:
        raise ValueError("Personal stats could not be found in the database")

    if not update_error and now - date_to_timestamp(ps.timestamp) > ESTIMATE_TTL:
        raise ValueError("Personal stats data is too old after an update")

    df = pd.DataFrame(columns=model_features, index=[0])

    for field_name in model_features:
        try:
            df[field_name][0] = ps.__getattribute__(field_name)
        except AttributeError:
            df[field_name][0] = 0

    df["tid"][0] = user_tid
    df = df.astype("int64")

    estimate = int(model().predict(df))
    redis_client.set(f"tornium:estimate:cache:{user_tid}", estimate, ex=ESTIMATE_TTL)

    return estimate, now - date_to_timestamp(ps.timestamp) + ESTIMATE_TTL
