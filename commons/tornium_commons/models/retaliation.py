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

from peewee import BigIntegerField, DateTimeField, FixedCharField, ForeignKeyField

from .base_model import BaseModel
from .user import User


class Retaliation(BaseModel):
    attack_code = FixedCharField(max_length=32, primary_key=True)  # Code of the attack according to the Torn API
    attack_ended = DateTimeField(null=False)
    defender = ForeignKeyField(User, null=False)
    attacker = ForeignKeyField(User, null=False)

    # Discord data related to the retal's notification
    message_id = BigIntegerField(null=False)
    channel_id = BigIntegerField(null=False)
