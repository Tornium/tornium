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
