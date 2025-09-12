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

from peewee import BigIntegerField, ForeignKeyField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel
from .faction import Faction
from .server import Server


class ServerOverdoseConfig(BaseModel):
    class Meta:
        table_name = "server_overdose_config"

    guid = UUIDField(primary_key=True)
    server = ForeignKeyField(Server, null=False)
    faction = ForeignKeyField(Faction, null=False)

    channel = BigIntegerField(default=None, null=True)

    def create_or_update(server_id: int, faction_id: int, **kwargs: dict):
        """
        Upsert data for a server and faction's OD configuration. The server ID and faction ID must not be included in the kwargs

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
        column_names = [name for name in ServerOverdoseConfig._meta.fields.keys()]

        for key in kwargs.keys():
            if key not in column_names:
                raise ValueError(f'Kwargs key "{key}" is not a column name of table "server_overdose_config"')
            elif key in ("server", "server_id", "faction", "faction_id"):
                raise ValueError(f'Kwargs key "{key}" can not be used in this function as it\'s a primary key')

        return (
            ServerOverdoseConfig.insert(guid=uuid.uuid4(), server=server_id, faction=faction_id, **kwargs)
            .on_conflict(
                conflict_target=[ServerOverdoseConfig.server, ServerOverdoseConfig.faction],
                preserve=[getattr(ServerOverdoseConfig, field) for field in kwargs.keys()],
            )
            .returning(ServerOverdoseConfig)
            .execute()
        )
