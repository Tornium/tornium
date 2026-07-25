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

import enum

from peewee import BooleanField, DateTimeField, ForeignKeyField, IntegerField, TextField

from .base_model import BaseModel
from .faction import Faction
from .item import Item
from .user import User


class ArmoryAction(enum.Enum):
    USE = "use"
    LOAN = "loan"
    RETURN = "return"
    FILL = "fill"
    GIVE = "give"
    RETRIEVE = "retrieve"


class ArmoryUsage(BaseModel):
    id = TextField(primary_key=True)
    timestamp = DateTimeField(null=False)
    action = TextField(null=False)
    # TODO: make `action` an enum
    # See https://github.com/coleifer/peewee/issues/630

    user = ForeignKeyField(User, null=False)
    recipient = ForeignKeyField(User, null=False)
    faction = ForeignKeyField(Faction, null=False)

    item = ForeignKeyField(Item, null=True)
    is_energy_refill = BooleanField(null=False)
    is_nerve_refill = BooleanField(null=False)

    quantity = IntegerField(null=False)

    class Meta:
        table_name = "armory_usage"

    def to_dict(self) -> dict:
        from ..formatters import timestamp

        return {
            "id": self.id,
            "timestamp": timestamp(self.timestamp),
            "action": self.action,
            "user": {
                "id": self.user_id,
                "name": User.user_name(self.user_id),
            },
            "recipient": {
                "id": self.recipient_id,
                "name": User.user_name(self.recipient_id),
            },
            "item": {
                "id": self.item_id,
                "name": None if self.item_id is None else Item.item_name(self.item_id),
                "is_nerve_refill": self.is_nerve_refill,
                "is_energy_refill": self.is_energy_refill,
                "quantity": self.quantity,
            },
        }
