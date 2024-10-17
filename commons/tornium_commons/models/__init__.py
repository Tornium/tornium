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

from .assist import Assist, AssistMessage
from .auth_log import AuthAction, AuthLog
from .faction import Faction
from .faction_position import FactionPosition
from .gateway_client import GatewayClient
from .gateway_message import GatewayMessage
from .item import Item
from .member_report import MemberReport
from .notification import Notification
from .notification_trigger import NotificationTrigger
from .oauth_authorization_code import OAuthAuthorizationCode
from .oauth_client import OAuthClient
from .oauth_token import OAuthToken
from .organized_crime import OrganizedCrime
from .personal_stats import PersonalStats
from .retaliation import Retaliation
from .server import Server
from .server_attack_config import ServerAttackConfig
from .stat import Stat
from .stock_tick import StockTick
from .torn_key import TornKey
from .user import User
from .withdrawal import Withdrawal

# NOTE: Non-model variables, classes, etc. can not be stored in __all__
# Otherwise the table won't be able to be generated

__all__ = [
    "Assist",
    "AssistMessage",
    "AuthLog",
    "Faction",
    "FactionPosition",
    "GatewayClient",
    "GatewayMessage",
    "Item",
    "MemberReport",
    "Notification",
    "NotificationTrigger",
    "OAuthAuthorizationCode",
    "OAuthClient",
    "OAuthToken",
    "OrganizedCrime",
    "PersonalStats",
    "Retaliation",
    "Server",
    "ServerAttackConfig",
    "Stat",
    "StockTick",
    "TornKey",
    "User",
    "Withdrawal",
]
