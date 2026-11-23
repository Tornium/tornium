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

import datetime
import inspect
import typing
from functools import cached_property, lru_cache

import statstimate
from peewee import (
    BigIntegerField,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DeferredForeignKey,
    DoesNotExist,
    FloatField,
    ForeignKeyField,
    IntegerField,
    SmallIntegerField,
    TextField,
)
from playhouse.postgres_ext import ArrayField

from ..errors import MissingKeyError
from ..estimator import ESTIMATOR
from .base_model import BaseModel
from .faction import Faction
from .faction_position import FactionPosition
from .personal_stats import PersonalStats
from .torn_key import TornKey

if typing.TYPE_CHECKING:
    from .stat import Stat


class User(BaseModel):
    class Meta:
        table_name = "user"

    # Basic data
    tid = IntegerField(primary_key=True)
    name = CharField(max_length=15, null=True)
    level = SmallIntegerField(null=True)
    discord_id = BigIntegerField(index=True, null=True)

    # Battle stats
    battlescore = FloatField(null=True)
    strength = BigIntegerField(null=True)
    defense = BigIntegerField(null=True)
    speed = BigIntegerField(null=True)
    dexterity = BigIntegerField(null=True)

    # Faction data
    faction = ForeignKeyField(Faction, index=True, null=True)
    faction_aa = BooleanField(default=False)
    faction_position = ForeignKeyField(FactionPosition, null=True)

    # User status
    status = TextField(null=True)
    last_action = DateTimeField(null=True)
    fedded_until = DateField(null=True)

    # Internal data
    last_refresh = DateTimeField(null=True)
    last_attacks = DateTimeField(null=True)
    battlescore_update = DateTimeField(null=True)

    # Security data
    security = SmallIntegerField(null=True)
    otp_secret = TextField(null=True)
    otp_backups = ArrayField(TextField, index=False, default=[])

    settings = DeferredForeignKey("UserSettings", default=None, null=True)

    @staticmethod
    def user_str(tid: int) -> str:
        if tid == -1:
            return "Someone"

        try:
            return f"{User.user_name(tid)} [{tid}]"
        except DoesNotExist:
            return f"N/A {tid}"

    @staticmethod
    @lru_cache
    def user_name(tid: int) -> str:
        try:
            return User.select(User.name).where(User.tid == tid).get().name
        except DoesNotExist:
            return "N/A"

    @staticmethod
    @lru_cache
    def user_discord_id(tid: int) -> int:
        return User.select(User.discord_id).where(User.tid == tid).get().discord_id

    def can_manage_crimes(self) -> bool:
        if self.faction_id is None:
            return False
        elif self.faction_position_id is None:
            return False

        faction_position: typing.Optional[FactionPosition] = self.faction_position

        if not isinstance(faction_position, FactionPosition):
            try:
                faction_position = (
                    FactionPosition.select(FactionPosition.permissions)
                    .where(FactionPosition.pid == self.faction_position_id)
                    .get()
                )
            except DoesNotExist:
                return False

        return "Organized Crimes" in faction_position.permissions

    def user_str_self(self) -> str:
        return f"{self.name} [{self.tid}]"

    def generate_otp_backups(self, num_codes=5):
        if self.otp_secret == "" or self.security != 1:  # nosec B105
            raise Exception("Illegal OTP secret or security mode")

    @cached_property
    def key(self) -> typing.Optional[str]:
        def _v(k):
            if k == "":
                return None
            return k

        api_keys = TornKey.select(TornKey.api_key).where(
            (TornKey.user_id == self.tid) & (TornKey.paused == False) & (TornKey.disabled == False)
        )
        keys_count = api_keys.count()

        if keys_count == 0:
            return None
        elif keys_count == 1:
            try:
                return _v(api_keys.get().api_key)
            except DoesNotExist:
                return None

        try:
            return _v(api_keys.where(TornKey.default == True).get().api_key)
        except DoesNotExist:
            pass

        try:
            return _v(api_keys.where(TornKey.access_level << [3, 4]).get().api_key)
        except DoesNotExist:
            return None

    @cached_property
    def personal_stats(self) -> typing.Optional[PersonalStats]:
        return (
            PersonalStats.select()
            .where(PersonalStats.user == self.tid)
            .order_by(PersonalStats.timestamp.desc())
            .first()
        )

    def personal_stats_at(
        self,
        timestamp: typing.Optional[datetime.datetime] = None,
        max_margin: datetime.timedelta = datetime.timedelta(days=1),
    ) -> typing.Optional[PersonalStats]:
        timestamp = timestamp or datetime.datetime.utcnow()

        return (
            PersonalStats.select()
            .where(
                (PersonalStats.user == self.tid)
                & (PersonalStats.timestamp.between(timestamp - max_margin, timestamp + max_margin))
            )
            .order_by(PersonalStats.timestamp.desc())
            .first()
        )

    def get_user_id(self) -> int:
        return self.tid

    def user_position_str(self) -> str:
        if self.faction is None:
            raise ValueError
        elif self.faction.leader_id == self.tid:
            return "Leader"
        elif self.faction.coleader_id == self.tid:
            return "Co-leader"
        elif self.faction_position is None:
            return "Unknown"

        return self.faction_position.name

    def to_dict(self) -> dict:
        return {
            "ID": self.tid,
            "name": self.name,
            "level": self.level,
            "discord_id": self.discord_id,
        }

    def user_embed(self) -> dict:
        embed = {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": f"{self.user_str_self()}",
                        "fields": [
                            {
                                "name": "Overview",
                                "value": inspect.cleandoc(f"""
                                    Level: {self.level}
                                    Last Action: <t:{int(self.last_action.timestamp())}:R>
                                    Last Update: <t:{int(self.last_refresh.timestamp())}:R>
                                """),
                            },
                        ],
                    },
                ],
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": "User Profile",
                                "url": f"https://www.torn.com/profiles.php?XID={self.tid}",
                            }
                        ],
                    }
                ],
                "flags": 64,
            },
        }

        if self.faction is not None:
            embed["data"]["embeds"][0]["fields"].append(
                {
                    "name": "Faction",
                    "value": inspect.cleandoc(f"""
                        Faction: [{self.faction.name} [{self.faction_id}]](https://www.torn.com/factions.php?step=profile&ID={self.faction_id}&referredFrom={self.tid})
                        Faction Position: {self.user_position_str()}
                    """),
                }
            )

        return embed

    @staticmethod
    def get_fedded_until(user_data: dict) -> typing.Optional[datetime.date]:
        """
        Get the date object representing when a user would leave federal jail.
        """

        if user_data["status"]["state"] == "Fallen":
            # A fallen user should be set to the maximum fed value of 9999-12-31
            return datetime.date(year=9999, month=12, day=31)
        elif user_data["status"]["state"] == "Federal" and "permanently" in user_data["status"]["description"]:
            return datetime.date(year=9999, month=12, day=31)
        elif user_data["status"]["state"] == "Federal":
            return datetime.date.fromtimestamp(user_data["status"]["until"])

        return None

    def stat(self, permitted_faction_id: typing.Optional[int] = None) -> typing.Optional["Stat"]:
        """
        Get the stats of the user from the stat database.

        If a permitted faction ID is provided, this indicates that the faction's stat database data
        can be used to find the latest stats of the user.

        Parameters
        ----------
        permitted_faction_id : typing.Optional[int]
            ID of the faction permitting access to their stats in the stat DB

        Returns
        -------
        typing.Optional[Stat]
            The latest stats of user if one could be found
        """

        from .stat import Stat

        query = Stat.select().where(Stat.tid == self.tid).order_by(Stat.time_added.desc())

        if permitted_faction_id is None:
            query = query.where(Stat.added_group.in_(0, permitted_faction_id))
        else:
            query = query.where(Stat.added_group == 0)

        return query.first()

    def estimate(
        self, permitted_faction_id: typing.Optional[int] = None, api_key: typing.Optional[str] = None
    ) -> statstimate.EstimatedStats:
        """
        Estimate the stats of the user from their personal stats and the stat database through the
        statstimate library.

        If a permitted faction ID is provided, this indicates that the faction's stat database data
        can be used to find the latest stats of the user.

        Parameters
        ----------
        permitted_faction_id : typing.Optional[int]
            ID of the faction permitting access to their stats in the stat DB

        api_key : typing.Optional[str]
            The API key of some user used to update the user's personal stats if necessary

        Returns
        -------
        statstimate.EstimatedStats
            An estimate of the user's stats.
        """

        from tornium_celery.tasks.user import update_user

        from .stat import Stat

        now = datetime.datetime.utcnow()
        latest_personal_stats: typing.Optional[PersonalStats] = self.personal_stats_at()

        if latest_personal_stats is None and api_key is None:
            raise MissingKeyError()
        elif latest_personal_stats is None:
            # If there were no personal stats, we need to fetch them through the API.

            r = update_user(tid=self.tid, refresh_existing=True, key=api_key)
            print(r)
            latest_personal_stats = self.personal_stats_at()
        if latest_personal_stats is None:
            # If there are still no personal stats found after potentially updating the database,
            # we cannot estimate the user's stats.

            raise LookupError("No current personal stats could be found")

        previous_stats_data: typing.Optional[Stat] = self.stat(permitted_faction_id=permitted_faction_id)

        previous_stats: typing.Optional[statstimate.PreviousStats] = None
        if previous_stats_data is not None:
            # If there were no personal stats, due to Torn's limitations in fetching historical data, we
            # cannot fetch new personal stats data for this time point. The statstimate library then will
            # only be able to use a snapshot model or retain the data from the previous stat DB entry.
            previous_personal_stats: typing.Optional[PersonalStats] = self.personal_stats_at(
                timestamp=previous_stats_data.time_added
            )

            if previous_personal_stats is not None:
                previous_stats = statstimate.PreviousStats(
                    stat_score=previous_stats_data.battlescore,
                    personal_stats=previous_personal_stats.to_dict(),
                    days_ago=(now - previous_stats_data.time_added).days,
                )

        return ESTIMATOR.estimate(
            personal_stats=None if latest_personal_stats is None else latest_personal_stats.to_dict(),
            previous_stats=previous_stats,
        )
