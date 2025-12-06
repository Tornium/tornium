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
from playhouse.postgres_ext import ArrayField, UUIDField

from .base_model import BaseModel
from .elimination_team import EliminationTeam
from .server import Server


class ServerVerificationEliminationConfig(BaseModel):
    guid = UUIDField(primary_key=True)
    server = ForeignKeyField(Server, null=False)
    team = ForeignKeyField(EliminationTeam, null=False)

    roles = ArrayField(BigIntegerField, index=False, default=[], null=False)

    class Meta:
        table_name = "server_verification_elimination_config"

    def create_or_update(server_id: int, team_id: str | uuid.UUID, **kwargs: dict):
        """
        Upsert data for user's settings. The user ID must not be included in the kwargs.

        NOTE: Assumes that the user ID has already been validated

        Parameters
        ----------
        server_id: int
            ID of the server
        team_id: str | uuid.UUID
            ID of the Elimination team
        kwargs : dict
            values of the user's settings to be upserted into the model
        """
        column_names = [name for name in ServerVerificationEliminationConfig._meta.fields.keys()]

        for key in kwargs.keys():
            if key not in column_names:
                raise ValueError(
                    f'Kwargs key "{key}" is not a column name of table "server_verification_elimination_config"'
                )
            elif key in ("guid",):
                raise ValueError(f'Kwargs key "{key}" can not be used in this function as it\'s a primary key')

        ServerVerificationEliminationConfig.insert(
            guid=uuid.uuid4(), server=server_id, team_id=team_id, **kwargs
        ).on_conflict(
            conflict_target=[ServerVerificationEliminationConfig.server, ServerVerificationEliminationConfig.team],
            preserve=[getattr(ServerVerificationEliminationConfig, field) for field in kwargs.keys()],
        ).returning(
            ServerVerificationEliminationConfig
        ).execute()[
            0
        ]

        # FIXME: Make this one query with a returning statement from the insert
        # return UserSettings.select().where(UserSettings.user == user_id).first()
        return None
