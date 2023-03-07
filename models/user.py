# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import base64
import hashlib
import os

from flask_login import UserMixin

from tornium_commons.models import UserModel


class User(UserMixin):
    def __init__(self, tid):
        """
        Retrieves the user from the database.

        :param tid: Torn user ID
        """

        user = UserModel.objects(_id=int(tid)).first()
        if user is None:
            raise ValueError("Unknown User")

        self.security = user.security
        self.otp_secret = user.otp_secret
        self.otp_backups = user.otp_backups

        self.tid = tid
        self.name = user.name
        self.level = user.level
        self.last_refresh = user.last_refresh
        self.admin = user.admin
        self.key = user.key
        self.battlescore = user.battlescore
        self.battlescore_update = user.battlescore_update
        self.strength = user.strength
        self.defense = user.defense
        self.speed = user.speed
        self.dexterity = user.dexterity

        self.discord_id = user.discord_id

        self.factiontid = user.factionid
        self.aa = user.factionaa
        self.faction_position = user.faction_position

        self.status = user.status
        self.last_action = user.last_action

    def get_id(self):
        return self.tid

    def generate_otp_secret(self):
        user: UserModel = UserModel.objects(tid=self.tid).first()
        user.otp_secret = base64.b32encode(os.urandom(10)).decode("utf-8")
        user.save()
        self.otp_secret = user.otp_secret

    def generate_otp_url(self):
        if self.otp_secret == "" or self.security != 1:  # nosec B105
            raise Exception("Illegal OTP secret or security mode")

        return f"otpauth://totp/Tornium:{self.tid}?secret={self.otp_secret}&Issuer=Tornium"

    def generate_otp_backups(self, num_codes=5):
        if self.otp_secret == "" or self.security != 1:  # nosec B105
            raise Exception("Illegal OTP secret or security mode")

        codes = []
        hashed_codes = []

        for _ in range(num_codes):
            codes.append(base64.b32encode(os.urandom(10)).decode("utf-8"))

        for code in codes:
            hashed_codes.append(hashlib.sha256(code.encode("utf-8")).hexdigest())

        user: UserModel = UserModel.objects(tid=self.tid).first()
        user.otp_backups = hashed_codes
        user.save()
        self.otp_backups = hashed_codes

        return codes
