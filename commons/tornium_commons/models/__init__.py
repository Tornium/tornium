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

from .auth_log import AuthAction, AuthLog
from .faction import Faction
from .faction_position import FactionPosition
from .item import Item
from .notification import Notification
from .notification_trigger import NotificationTrigger
from .oauth_authorization_code import OAuthAuthorizationCode
from .oauth_client import OAuthClient
from .oauth_token import OAuthToken
from .organized_crime import OrganizedCrime
from .organized_crime_cpr import OrganizedCrimeCPR
from .organized_crime_new import OrganizedCrimeNew
from .organized_crime_slot import OrganizedCrimeSlot
from .organized_crime_team import OrganizedCrimeTeam
from .organized_crime_team_member import OrganizedCrimeTeamMember
from .personal_stats import PersonalStats
from .retaliation import Retaliation
from .server import Server
from .server_attack_config import ServerAttackConfig
from .server_notifications_config import ServerNotificationsConfig
from .server_oc_config import ServerOCConfig
from .server_oc_range_config import ServerOCRangeConfig
from .stat import Stat
from .stock_tick import StockTick
from .torn_key import TornKey
from .user import User
from .user_settings import UserSettings
from .withdrawal import Withdrawal

# NOTE: Non-model variables, classes, etc. can not be stored in __all__
# Otherwise the table won't be able to be generated

__all__ = [
    "AuthLog",
    "Faction",
    "FactionPosition",
    "Item",
    "Notification",
    "NotificationTrigger",
    "OAuthAuthorizationCode",
    "OAuthClient",
    "OAuthToken",
    "OrganizedCrime",
    "OrganizedCrimeCPR",
    "OrganizedCrimeNew",
    "OrganizedCrimeSlot",
    "OrganizedCrimeTeam",
    "OrganizedCrimeTeamMember",
    "PersonalStats",
    "Retaliation",
    "Server",
    "ServerAttackConfig",
    "ServerNotificationsConfig",
    "ServerOCConfig",
    "ServerOCRangeConfig",
    "Stat",
    "StockTick",
    "TornKey",
    "User",
    "UserSettings",
    "Withdrawal",
]
