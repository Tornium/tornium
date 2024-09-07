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

import math
import typing

from peewee import DateTimeField, ForeignKeyField, IntegerField

from ..db_connection import db
from .base_model import BaseModel
from .user import User

_DIFFICULTY_MAP = {
    0: (1.25, 1.75),
    1: (1.75, 2),
    2: (2, 2.25),
    3: (2.25, 2.5),
    4: (2.5, 3),
    5: (3, 3.4),
}


class Stat(BaseModel):
    tid = ForeignKeyField(User)
    battlescore = IntegerField(index=True)
    time_added = DateTimeField()
    added_group = IntegerField(default=0, index=True)

    # Groups
    # 0 - universally accepted
    # faction tid - for specific factions

    @staticmethod
    def generate_chain_list(
        sort: typing.Literal["timestamp", "random", "respect"],
        difficulty: typing.Literal[0, 1, 2, 3, 4, 5],
        limit: int,
        invoker: User,
    ) -> list:
        if difficulty not in (0, 1, 2, 3, 4, 5):
            raise ValueError("Illegal difficulty value") from None
        elif not (1 <= limit <= 100):
            raise ValueError("Illegal limit value") from None

        if invoker is None:
            raise ValueError("User does not exist") from None
        elif invoker.battlescore == 0 or invoker.battlescore is None:
            raise ValueError("User does not have a battlescore") from None

        # f = fair fight
        # v = variance
        # d = defender's stat score
        # a = attacker's stat score
        #
        # f +- v = 1 + 8/3 * d/a
        # 0.375 * a * (f +- v - 1) = d
        #
        # f = 11/3 is equal ratio of d/a
        # f = 17/5 is 9/10 ratio of d/a

        # Difficulty | Min FF | Max FF |     Name    |
        #     0      |  1.25  |  1.75  |  Very Easy  |
        #     1      |  1.75  |   2    |    Easy     |
        #     2      |   2    |  2.25  |   Medium    |
        #     3      |  2.25  |  2.5   |    Hard     |
        #     4      |  2.5   |   3    |  Very Hard  |
        #     5      |   3    |  3.4   |  Formidable |
        #
        # In the equation, 3x FF is equivalent to times 2.4 which is 3.4 - 1

        min_ff, max_ff = _DIFFICULTY_MAP[difficulty]
        parameters = [
            invoker.faction_id,
            int(0.375 * invoker.battlescore * (min_ff - 1)),
            int(0.375 * invoker.battlescore * (max_ff - 1)),
            limit,
        ]

        # Paramter order
        # 0 = added faction
        # 1 = min battlescore
        # 2 = max battlescore
        # 3 = limit

        if sort == "timestamp":
            query = """select "t1"."id", "t1"."tid_id", "t1"."time_added", "t1"."battlescore", "t2"."name", "t2"."level", "t2"."last_refresh", "t2"."faction_id", "t2"."status", "t2"."last_action", "t3"."name" from (select * from (select distinct on ("t1"."tid_id") * from "stat" as "t1" where ("t1"."added_group" = 0) or ("t1"."added_group" = %s) order by "t1"."tid_id", "t1"."time_added" desc) t1 where ("t1"."battlescore" >= %s) and ("t1"."battlescore" <= %s)) t1 join "user" as "t2" on "t2"."tid" = "t1"."tid_id" left join "faction" as "t3" on "t3"."tid" = "t2"."faction_id" where "t2"."level" is not null order by "t1"."time_added" desc limit %s"""
        elif sort == "random":
            query = """select "t1"."id", "t1"."tid_id", "t1"."time_added", "t1"."battlescore", "t2"."name", "t2"."level", "t2"."last_refresh", "t2"."faction_id", "t2"."status", "t2"."last_action", "t3"."name"  from (select * from (select distinct on ("t1"."tid_id") * from "stat" as "t1" where ("t1"."added_group" = 0) or ("t1"."added_group" = %s) order by "t1"."tid_id", "t1"."time_added" desc) t1 where ("t1"."battlescore" >= %s) and ("t1"."battlescore" <= %s)) t1 join "user" as "t2" on "t2"."tid" = "t1"."tid_id" left join "faction" as "t3" on "t3"."tid" = "t2"."faction_id" where "t2"."level" is not null and "t1"."time_added" > now() - interval '3 months' order by random() limit %s"""
        else:  # Sorted by respect
            query = f"""select "t1"."id", "t1"."tid_id", "t1"."time_added", "t1"."battlescore", "t2"."name", "t2"."level", "t2"."last_refresh", "t2"."faction_id", "t2"."status", "t2"."last_action", "t3"."name"  from (select * from (select distinct on ("t1"."tid_id") * from "stat" as "t1" where ("t1"."added_group" = 0) or ("t1"."added_group" = %s) order by "t1"."tid_id", "t1"."time_added" desc) t1 where ("t1"."battlescore" >= %s) and ("t1"."battlescore" <= %s)) t1 join "user" as "t2" on "t2"."tid" = "t1"."tid_id" left join "faction" as "t3" on "t3"."tid" = "t2"."faction_id" where "t2"."level" is not null and "t1"."time_added" > now() - interval '3 months' order by ((("t2"."level" / 198) + 197/198) * least(1 + 8 / 3 * ("t1"."battlescore" / {int(invoker.battlescore)}), 3)) desc, "t1"."time_added" desc limit %s"""
            # TODO: Make the query store the FF and respect in the query result

        stat_entries = []

        for stat_entry in db().execute_sql(query, parameters):
            target_ff = round(1 + 8 / 3 * (stat_entry[3] / invoker.battlescore), 2)

            if target_ff > 3:
                target_ff = 3
            if stat_entry[1] is None or stat_entry[5] in (0, None):
                continue

            try:
                base_respect = round(stat_entry[5] / 198 + 197 / 198, 2)
            except ValueError:
                continue

            stat_entries.append(
                {
                    "statid": stat_entry[0],
                    "tid": stat_entry[1],
                    "battlescore": stat_entry[3],
                    "timeadded": stat_entry[2].timestamp(),
                    "ff": target_ff,
                    "respect": round(base_respect * target_ff, 2),
                    "user": {
                        "tid": stat_entry[1],
                        "name": stat_entry[4],
                        "username": f"{stat_entry[4]} [{stat_entry[1]}]",
                        "level": stat_entry[5],
                        "last_refresh": (stat_entry[6].timestamp() if stat_entry[6] is not None else None),
                        "faction": {
                            "tid": stat_entry[7],
                            "name": stat_entry[10],
                        },
                        "status": stat_entry[8],
                        "last_action": stat_entry[9].timestamp(),
                    },
                }
            )

        return stat_entries
