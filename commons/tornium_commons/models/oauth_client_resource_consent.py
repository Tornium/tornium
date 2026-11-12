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

import datetime
import typing

from peewee import DateTimeField, ForeignKeyField, TextField
from playhouse.postgres_ext import UUIDField

from .base_model import BaseModel
from .faction import Faction
from .oauth_client import OAuthClient
from .server import Server
from .user import User


class OAuthClientResourceConsent(BaseModel):
    class Meta:
        table_name = "oauth_client_resource_consent"

    guid = UUIDField(primary_key=True)

    client = ForeignKeyField(OAuthClient, backref="consents", null=False)
    scope = TextField(default="", null=False)

    faction = ForeignKeyField(Faction, default=None, null=True)
    server = ForeignKeyField(Server, default=None, null=True)

    consented_by = ForeignKeyField(User, null=False)
    consented_at = DateTimeField(default=datetime.datetime.utcnow, null=False)
    revoked_by = ForeignKeyField(User, default=None, null=True)
    revoked_at = DateTimeField(default=None, null=True)

    RESOURCE_TYPES = ("faction", "server")

    @classmethod
    def get_consent(cls, client_id: str, **kwargs) -> typing.Optional["OAuthClientResourceConsent"]:
        """
        Check and get if a resource (e.g. a faction) actively provides consent.

        Parameters
        ----------
        client_id : str
            ID of the OAuth client

        **kwargs
            Dictionary of `cls.RESOURCE_TYPES` to the resource ID. There should only be one
            resource type provided though.

        Returns
        -------
        typing.Optional["OAuthClientResourceConsent"]
            The active consent of the resource if one exists.
        """

        configured_resource_types: typing.Dict[str, int] = {
            resource_type: kwargs[resource_type]
            for resource_type in cls.RESOURCE_TYPES
            if kwargs.get(resource_type) is not None and isinstance(kwargs[resource_type], int)
        }

        if len(configured_resource_types) != 1:
            raise ValueError(
                f"There were {len(configured_resource_types)} resource types provided when only 1 was expected."
            )

        configured_resource_type = next(iter(configured_resource_types))
        configured_resource_id = configured_resource_types[configured_resource_type]

        return (
            cls.select()
            .where(
                (cls.client == client_id)
                & (cls.revoked_at.is_null(True))
                & (cls.revoked_by.is_null(True))
                & (getattr(cls, configured_resource_type) == configured_resource_id)
            )
            .first()
        )
