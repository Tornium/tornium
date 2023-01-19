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

from mongoengine import BooleanField, Document, IntField, StringField, UUIDField


class PositionModel(Document):
    meta = {"indexes": ["#name", "factiontid", "+canAccessFactionApi", "+canGiveMoney"]}

    pid = UUIDField(primary_key=True)
    name = StringField(required=True)
    factiontid = IntField(required=True)

    default = BooleanField(default=False)

    # Permissions
    canUseMedicalItem = BooleanField(default=False)
    canUseBoosterItem = BooleanField(default=False)
    canUseDrugItem = BooleanField(default=False)
    canUseEnergyRefill = BooleanField(default=False)
    canUseNerveRefill = BooleanField(default=False)
    canLoanTemporaryItem = BooleanField(default=False)
    canLoanWeaponAndArmory = BooleanField(default=False)
    canRetrieveLoanedArmory = BooleanField(default=False)
    canPlanAndInitiateOrganisedCrime = BooleanField(default=False)
    canAccessFactionApi = BooleanField(default=False)
    canGiveItem = BooleanField(default=False)
    canGiveMoney = BooleanField(default=False)
    canGivePoints = BooleanField(default=False)
    canManageForum = BooleanField(default=False)
    canManageApplications = BooleanField(default=False)
    canKickMembers = BooleanField(default=False)
    canAdjustMemberBalance = BooleanField(default=False)
    canManageWars = BooleanField(default=False)
    canManageUpgrades = BooleanField(default=False)
    canSendNewsletter = BooleanField(default=False)
    canChangeAnnouncement = BooleanField(default=False)
    canChangeDescription = BooleanField(default=False)
