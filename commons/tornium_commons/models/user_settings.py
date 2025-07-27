# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import uuid

from peewee import BooleanField, ForeignKeyField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel
from .user import User


class UserSettings(BaseModel):
    class Meta:
        table_name = "user_settings"

    guid = UUIDField(primary_key=True)
    user = ForeignKeyField(User, unique=True)

    cpr_enabled = BooleanField(default=True, null=False)

    def create_or_update(user_id: int, **kwargs: dict):
        """
        Upsert data for user's settings. The user ID must not be included in the kwargs.

        NOTE: Assumes that the user ID has already been validated

        Parameters
        ----------
        user: int
            ID of the user
        kwargs : dict
            values of the user's settings to be upserted into the model
        """
        column_names = [name for name in UserSettings._meta.fields.keys()]

        for key in kwargs.keys():
            if key not in column_names:
                raise ValueError(f'Kwargs key "{key}" is not a column name of table "user_settings"')
            elif key in ("user", "user_id", "guid"):
                raise ValueError(f'Kwargs key "{key}" can not be used in this function as it\'s a primary key')

        settings = (
            UserSettings.insert(guid=uuid.uuid4(), user=user_id, **kwargs)
            .on_conflict(
                conflict_target=[UserSettings.user], preserve=[getattr(UserSettings, field) for field in kwargs.keys()]
            )
            .returning(UserSettings)
            .execute()[0]
        )

        User.update(settings=settings).where(User.tid == user_id).execute()

        # FIXME: Make this one query with a returning statement from the insert
        # return UserSettings.select().where(UserSettings.user == user_id).first()
        return settings

    def to_dict(self) -> dict:
        return {
            "guid": self.guid,
            "cpr_enabled": self.cpr_enabled,
        }
