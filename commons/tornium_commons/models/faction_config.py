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

from __future__ import annotations

import typing
import uuid

from peewee import BooleanField, ForeignKeyField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel
from .faction import Faction


class FactionConfig(BaseModel):
    class Meta:
        table_name = "faction_config"

    guid = UUIDField(primary_key=True)
    faction = ForeignKeyField(Faction, null=False, backref="config", unique=True)

    ts_stats_enabled = BooleanField(default=True, null=False)

    def create_or_update(faction_id: int, **kwargs: dict) -> typing.Optional[FactionConfig]:
        """
        Upsert data for the faction's setting configuration. The faction ID must not be included in
        the kwargs.

        NOTE: Assumes that the faction ID has already been validated.

        Parameters
        ----------
        faction_id: int
            ID of the faction
        kwargs : dict
            Values of the faction's config to be upserted into the model
        """

        column_names = [name for name in FactionConfig._meta.fields.keys()]

        for key in kwargs.keys():
            if key not in column_names:
                raise ValueError(f'Kwargs key "{key}" is not a column name of table "faction_config"')
            elif key in ("faction", "faction_id", "guid"):
                raise ValueError(f'Kwargs key "{key}" can not be used in this function as it\'s a primary key')

        config_query = FactionConfig.insert(guid=uuid.uuid4(), faction_id=faction_id, **kwargs)

        if len(kwargs) == 0:
            config_query = config_query.on_conflict_ignore()
        else:
            config_query = config_query.on_conflict(
                conflict_target=[FactionConfig.faction_id],
                preserve=[getattr(FactionConfig, field) for field in kwargs.keys()],
            )

        config = config_query.returning(FactionConfig).execute()[0]
        print(config)

        return config

    def to_dict(self) -> dict:
        return {"guid": self.guid, "ts_stats_enabled": self.ts_stats_enabled}
