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

from peewee import (
    BigIntegerField,
    BooleanField,
    CharField,
    ForeignKeyField,
    SmallIntegerField,
)
from playhouse.postgres_ext import ArrayField, UUIDField

from .base_model import BaseModel
from .faction import Faction
from .server import Server


class ServerOCConfig(BaseModel):
    class Meta:
        table_name = "server_oc_config"

    guid = UUIDField(primary_key=True)
    server = ForeignKeyField(Server, null=False)
    faction = ForeignKeyField(Faction, null=False)
    enabled = BooleanField(default=False, null=False)

    # Missing tools/materials for an OC
    tool_channel = BigIntegerField(default=None, null=True)
    tool_roles = ArrayField(BigIntegerField, index=False, default=[])
    tool_crimes = ArrayField(CharField, index=False, default=[])

    # Delayed OCs
    delayed_channel = BigIntegerField(default=None, null=True)
    delayed_roles = ArrayField(BigIntegerField, index=False, default=[])
    delayed_crimes = ArrayField(CharField, index=False, default=[])

    # Extra-range OCs
    extra_range_channel = BigIntegerField(default=None, null=True)
    extra_range_roles = ArrayField(BigIntegerField, index=False, default=[])
    extra_range_global_min = SmallIntegerField(default=0, null=False)
    extra_range_global_max = SmallIntegerField(default=100, null=False)

    def create_or_update(server_id: int, faction_id: int, **kwargs: dict):
        """
        Upsert data for a server and faction's OC configuration. The server ID and faction ID must not be included in the kwargs

        NOTE: Assumes that the server ID and faction ID have already been validated

        Parameters
        ----------
        server_id : int
            ID of the server
        faction_id : int
            ID of the faction
        kwargs : dict
            values to be upserted into the model
        """
        column_names = [name for name in ServerOCConfig._meta.fields.keys()]

        for key in kwargs.keys():
            if key not in column_names:
                raise ValueError(f'Kwargs key "{key}" is not a column name of table "server_oc_config"')
            elif key in ("server", "server_id", "faction", "faction_id"):
                raise ValueError(f'Kwargs key "{key}" can not be used in this function as it\'s a primary key')

        ServerOCConfig.insert(guid=uuid.uuid4(), server=server_id, faction=faction_id, **kwargs).on_conflict(
            conflict_target=[ServerOCConfig.server, ServerOCConfig.faction],
            preserve=[getattr(ServerOCConfig, field) for field in kwargs.keys()],
        ).execute()

        # FIXME: Make this one query with a returning statement from the insert
        return (
            ServerOCConfig.select()
            .where((ServerOCConfig.server == server_id) & (ServerOCConfig.faction == faction_id))
            .first()
        )

    def to_dict(self) -> dict:
        return {
            "guid": self.guid,
            "server_id": self.server_id,
            "faction_id": self.faction_id,
            "enabled": self.enabled,
            "tool_channel": self.tool_channel,
            "tool_roles": self.tool_roles,
            "tool_crimes": self.tool_crimes,
            "delayed_channel": self.delayed_channel,
            "delayed_roles": self.delayed_roles,
            "delayed_crimes": self.delayed_crimes,
            "extra_range_channel": self.extra_range_channel,
            "extra_range_roles": self.extra_range_roles,
            "extra_range_global_min": self.extra_range_global_min,
            "extra_range_global_max": self.extra_range_global_max,
        }
