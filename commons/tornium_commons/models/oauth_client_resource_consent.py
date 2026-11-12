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

from authlib.oauth2.rfc6749 import list_to_scope, scope_to_list
from peewee import DateTimeField, ForeignKeyField, TextField
from playhouse.postgres_ext import UUIDField

from ..db_connection import db
from .auth_log import AuthAction, AuthLog
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

    @property
    def resource(self) -> typing.Tuple[str, int]:
        if self.faction_id:
            return ("faction", self.faction_id)
        elif self.server_id:
            return ("server", self.server_id)

        raise ValueError(f"Unable to determine resource type of consent {self.guid}")

    @property
    def scopes(self) -> typing.List[str]:
        return scope_to_list(self.scope)

    @staticmethod
    def is_allowed_consent(user: User, resource_type: str, resource_id: int) -> bool:
        if resource_type == "faction":
            return (
                user.faction_id == resource_id
                and user.faction_position is not None
                and user.faction_position.name in ("Leader", "Co-leader")
            )
        elif resource_type == "server":
            return Server.select().where((Server.sid == resource_id) & (Server.admins.contains(user.tid))).exists()

        raise ValueError(f"Invalid resource type {resource_type}")

    @classmethod
    @db.atomic()
    def grant(
        cls, client_id: str, user: User, resource_type: str, resource_id: int, scopes: set[str]
    ) -> "OAuthClientResourceConsent":
        existing_consent = cls.get_consent(client_id, **{resource_type: resource_id})

        if existing_consent is not None and set(scope_to_list(existing_consent.scope)) == scopes:
            # Nothing has changed in the scopes between the existing consent and the
            # requested granting of a consent, so we can just give the existing consent.
            return existing_consent
        elif existing_consent is not None:
            # There is some difference between the existing consent's scopes and what scopes
            # have been requested, so we can replace the existing one for a new one (by
            # revoking it first).
            existing_consent.revoke(user)

        consent = cls.create(
            client=client_id,
            scope=list_to_scope(sorted(scopes)),
            consented_by=user.tid,
            **{resource_type: resource_id},
        )

        AuthLog.insert(
            user=user.tid,
            action=AuthAction.OAUTH_CONSENT_GRANT.value,
            details=f"{client_id} {resource_type}:{resource_id}",
        ).execute()

        return consent

    @db.atomic()
    def revoke(self, user: User):
        from .oauth_token import OAuthToken

        now = datetime.datetime.utcnow()

        # We want to revoke the consent and the OAuth token attached to the consent
        # when it's revoked as the OAuth token is unable to be used without the consent.
        OAuthClientResourceConsent.update(revoked_at=now, revoked_by=user.tid).where(
            (OAuthClientResourceConsent.guid == self.guid) & (OAuthClientResourceConsent.revoked_at.is_null(True))
        ).execute()
        OAuthToken.update(access_token_revoked_at=now).where(
            (OAuthToken.consent == self.guid) & (OAuthToken.access_token_revoked_at.is_null(True))
        ).execute()

        AuthLog.insert(
            user=user.tid,
            action=AuthAction.OAUTH_CONSENT_REVOKE.value,
            details=f"{self.client_id} {self.resource[0]}:{self.resource[1]}",
        ).execute()
