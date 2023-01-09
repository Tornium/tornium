# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

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
