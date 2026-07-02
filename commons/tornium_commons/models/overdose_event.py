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

from peewee import DateTimeField, ForeignKeyField, UUIDField

from .base_model import BaseModel
from .faction import Faction
from .item import Item
from .user import User


class OverdoseEvent(BaseModel):
    class Meta:
        table_name = "overdose_event"

    guid = UUIDField(primary_key=True)

    faction = ForeignKeyField(Faction, null=False)
    user = ForeignKeyField(User, null=False)

    created_at = DateTimeField(null=False)
    notified_at = DateTimeField(default=None, null=True)

    drug = ForeignKeyField(Item, null=True)

    def to_dict(self) -> dict:
        from ..formatters import timestamp

        return {
            "id": self.guid,
            "user": {
                "id": self.user_id,
                "name": self.user.name,
            },
            "timestamp": timestamp(self.created_at),
            "drug": (
                {
                    "id": self.drug_id,
                    "name": self.drug.name,
                }
                if self.drug_id
                else None
            ),
        }
