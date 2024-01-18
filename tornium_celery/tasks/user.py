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

import datetime
import math
import time
import typing
from decimal import DivisionByZero

import celery
from celery.utils.log import get_task_logger
from peewee import DoesNotExist, fn
from tornium_commons import rds
from tornium_commons.errors import MissingKeyError, NetworkingError, TornError
from tornium_commons.models import Faction, FactionPosition, PersonalStats, Stat, User

from .api import tornget

logger = get_task_logger("celery_app")

MIN_USER_UPDATE = 600


@celery.shared_task(
    name="tasks.user.update_user",
    routing_key="default.update_user",
    queue="default",
    bind=True,
    time_limit=10,
)
def update_user(self: celery.Task, key: str, tid: int = 0, discordid: int = 0, refresh_existing=True):
    # TODO: Change default values of tid and discordid to None
    # TODO: Refactor discordid -> discord_id

    if key is None or key == "":
        raise MissingKeyError
    elif tid != 0 and discordid != 0:
        raise Exception("No valid user ID passed")

    update_self = False
    user_exists = None
    user: typing.Optional[User] = None

    if tid != 0:
        user = User.select(User.last_refresh).where(User.tid == tid).first()
        user_exists = user is not None

        if (
            user is not None
            and user.last_refresh is not None
            and time.time() - user.last_refresh.timestamp() <= MIN_USER_UPDATE
        ):
            return

        user_id = tid
    elif discordid == tid == 0:
        user = User.select(User.last_refresh).where(User.key == key).first()

        if (
            user is not None
            and user.last_refresh is not None
            and time.time() - user.last_refresh.timestamp() <= MIN_USER_UPDATE
        ):
            return

        user_id = 0
        update_self = True
    else:
        user = User.select(User.last_refresh).where(User.tid == tid).first()
        user_exists = user is not None

        if (
            user is not None
            and user.last_refresh is not None
            and time.time() - user.last_refresh.timestamp() <= MIN_USER_UPDATE
        ):
            return

        user_id = discordid

    if user_exists and not refresh_existing:
        return
    elif user is not None and not refresh_existing:
        return

    result_sig: celery.canvas.Signature
    if update_self:
        result_sig = tornget.signature(
            kwargs={
                "endpoint": f"user/{user_id}?selections=profile,discord,personalstats,battlestats",
                "key": key,
            },
            queue="api",
        )
    else:
        result_sig = tornget.signature(
            kwargs={
                "endpoint": f"user/{user_id}?selections=profile,discord,personalstats",
                "key": user.key if user is not None and user.key not in (None, "") else key,
            },
            queue="api",
        )

    if self.request.id is None:  # Run in same process
        api_result = result_sig()

        if update_self:
            result = update_user_self(api_result, key=key)
        else:
            result = update_user_other(api_result)

        return result
    else:  # Run in a Celery worker
        if update_self:
            result = result_sig.apply_async(expires=300, link=update_user_self.signature(kwargs={"key": key}))
        else:
            result = result_sig.apply_async(expires=300, link=update_user_other.s())


@celery.shared_task(
    name="tasks.user.update_user_self",
    routing_key="quick.update_user_self",
    queue="quick",
    time_limit=10,
)
def update_user_self(user_data, key=None):
    user_data_kwargs = {"faction_aa": False}

    if key is not None:
        user_data_kwargs["key"] = key

    faction: typing.Optional[Faction]
    if user_data["faction"]["faction_id"] != 0:
        faction = (
            Faction.insert(
                tid=user_data["faction"]["faction_id"],
                name=user_data["faction"]["faction_name"],
                tag=user_data["faction"]["faction_tag"],
            )
            .on_conflict(
                conflict_target=[Faction.tid],
                preserve=[Faction.name, Faction.tag],
            )
            .execute()
        )

        if key is not None:
            faction = Faction.select(Faction.aa_keys).where(Faction.tid == user_data["faction"]["faction_id"]).first()

            if faction is not None and len(faction.aa_keys) == 0:
                from .faction import update_faction_positions

                try:
                    positions_data = tornget("faction/?selections=basic,positions", key)
                except TornError as e:
                    if e.code == 7:
                        user_data_kwargs["faction_aa"] = False
                except NetworkingError:
                    pass
                else:
                    user_data_kwargs["faction_aa"] = True
                    update_faction_positions(positions_data)

        if user_data["faction"]["position"] in ("Leader", "Co-leader"):
            user_data_kwargs["faction_position"] = None
            user_data_kwargs["faction_aa"] = True

            if user_data["faction"]["position"] == "Leader":
                Faction.update(leader=user_data["player_id"]).where(tid=user_data["faction"]["faction_id"]).execute()
            elif user_data["faction"]["position"] == "Co-leader":
                Faction.update(coleader=user_data["player_id"]).where(tid=user_data["faction"]["faction_id"]).execute()
        elif user_data["faction"]["position"] not in (
            "None",
            "Recruit",
            "Leader",
            "Co-leader",
        ):
            faction_position: typing.Optional[FactionPosition] = (
                FactionPosition.select()
                .where(
                    (FactionPosition.name == user_data["faction"]["position"])
                    & (FactionPosition.faction_tid == user_data["faction"]["faction_id"])
                )
                .first()
            )

            if faction_position is None:
                user_data_kwargs["faction_position"] = None
                user_data_kwargs["faction_aa"] = False
            else:
                user_data_kwargs["faction_position"] = faction_position
                user_data_kwargs["faction_aa"] = faction_position.access_fac_api
    else:
        faction = None
        user_data_kwargs["faction_position"] = None
        user_data_kwargs["faction_aa"] = False

    if "personalstats" in user_data:
        now: datetime.datetime = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        pstat_id = int(bin(user_data["player_id"] << 8), 2) + int(bin(int(now.timestamp())), 2)

        PersonalStats.insert(
            pstat_id=pstat_id,
            tid=user_data["player_id"],
            timestamp=now,
            **{k: v for k, v in user_data["personalstats"].items() if k in PersonalStats._meta.sorted_field_names},
        ).on_conflict(
            conflict_target=[PersonalStats.pstat_id],
            preserve=[
                PersonalStats.timestamp,
                *(
                    getattr(PersonalStats, k)
                    for k in user_data["personalstats"].keys()
                    if k in PersonalStats._meta.sorted_field_names
                ),
            ],
        ).execute()

        stored_ps: typing.Optional[PersonalStats] = (
            PersonalStats.select().where(PersonalStats.pstat_id == pstat_id).first()
        )

        if (
            stored_ps is not None
            and len(
                set(PersonalStats._meta.sorted_field_names)
                - set(k for k in PersonalStats._meta.sorted_field_names if getattr(stored_ps, k) is not None)
            )
            == 0
        ):
            user_data_kwargs["personal_stats"] = pstat_id

    User.insert(
        tid=user_data["player_id"],
        name=user_data["name"],
        level=user_data["level"],
        discord_id=user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0,
        battlescore=(
            math.sqrt(user_data["strength"])
            + math.sqrt(user_data["defense"])
            + math.sqrt(user_data["speed"])
            + math.sqrt(user_data["dexterity"])
        ),
        strength=user_data["strength"],
        defense=user_data["defense"],
        speed=user_data["speed"],
        dexterity=user_data["dexterity"],
        faction=faction,
        status=user_data["last_action"]["status"],
        last_action=datetime.datetime.fromtimestamp(user_data["last_action"]["timestamp"], tz=datetime.timezone.utc),
        last_refresh=datetime.datetime.utcnow(),
        battlescore_update=datetime.datetime.utcnow(),
        **user_data_kwargs,
    ).on_conflict(
        conflict_target=[User.tid],
        preserve=[
            User.name,
            User.level,
            User.discord_id,
            User.battlescore,
            User.strength,
            User.defense,
            User.speed,
            User.dexterity,
            User.faction,
            User.status,
            User.last_action,
            User.last_refresh,
            User.battlescore_update,
            *(getattr(User, k) for k in user_data_kwargs.keys()),
        ],
    ).execute()

    if user_data_kwargs.get("faction_aa"):
        _faction = Faction.select(Faction.aa_keys).where(Faction.tid == user_data["faction"]["faction_id"]).first()

        if _faction is not None and key is not None and key not in _faction.aa_keys:
            Faction.update(aa_keys=fn.array_append(Faction.aa_keys, key)).where(
                Faction.tid == user_data["faction"]["faction_id"]
            ).execute()


@celery.shared_task(
    name="tasks.user.update_user_other",
    routing_key="quick.update_user_other",
    queue="quick",
    time_limit=5,
)
def update_user_other(user_data):
    user_data_kwargs = {"faction_aa": False}

    faction: typing.Optional[Faction]
    if user_data["faction"]["faction_id"] != 0:
        faction = (
            Faction.insert(
                tid=user_data["faction"]["faction_id"],
                name=user_data["faction"]["faction_name"],
                tag=user_data["faction"]["faction_tag"],
            )
            .on_conflict(
                conflict_target=[Faction.tid],
                preserve=[Faction.name, Faction.tag],
            )
            .execute()
        )

        if user_data["faction"]["position"] in ("Leader", "Co-leader"):
            user_data_kwargs["faction_position"] = None
            user_data_kwargs["faction_aa"] = True

            if user_data["faction"]["position"] == "Leader":
                Faction.update(leader=user_data["player_id"]).where(tid=user_data["faction"]["faction_id"]).execute()
            elif user_data["faction"]["position"] == "Co-leader":
                Faction.update(coleader=user_data["player_id"]).where(tid=user_data["faction"]["faction_id"]).execute()
        elif user_data["faction"]["position"] not in (
            "None",
            "Recruit",
            "Leader",
            "Co-leader",
        ):
            faction_position: typing.Optional[FactionPosition] = (
                FactionPosition.select()
                .where(
                    (FactionPosition.name == user_data["faction"]["position"])
                    & (FactionPosition.faction_tid == user_data["faction"]["faction_id"])
                )
                .first()
            )

            if faction_position is None:
                user_data_kwargs["faction_position"] = None

                user_data_kwargs["faction_aa"] = False
            else:
                user_data_kwargs["faction_position"] = faction_position
                user_data_kwargs["faction_aa"] = faction_position.access_fac_api
    else:
        faction = None
        user_data_kwargs["faction_position"] = None
        user_data_kwargs["faction_aa"] = False

    if "personalstats" in user_data:
        now: datetime.datetime = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        pstat_id = int(bin(user_data["player_id"] << 8), 2) + int(bin(int(now.timestamp())), 2)

        PersonalStats.insert(
            pstat_id=pstat_id,
            tid=user_data["player_id"],
            timestamp=now,
            **{k: v for k, v in user_data["personalstats"].items() if k in PersonalStats._meta.sorted_field_names},
        ).on_conflict(
            conflict_target=[PersonalStats.pstat_id],
            preserve=[
                PersonalStats.timestamp,
                *(
                    getattr(PersonalStats, k)
                    for k in user_data["personalstats"].keys()
                    if k in PersonalStats._meta.sorted_field_names
                ),
            ],
        ).execute()

        stored_ps: typing.Optional[PersonalStats] = (
            PersonalStats.select().where(PersonalStats.pstat_id == pstat_id).first()
        )

        if (
            stored_ps is not None
            and len(
                set(PersonalStats._meta.sorted_field_names)
                - set(k for k in PersonalStats._meta.sorted_field_names if getattr(stored_ps, k) is not None)
            )
            == 0
        ):
            user_data_kwargs["personal_stats"] = pstat_id

    User.insert(
        tid=user_data["player_id"],
        name=user_data["name"],
        level=user_data["level"],
        discord_id=user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0,
        faction=faction,
        status=user_data["last_action"]["status"],
        last_action=datetime.datetime.fromtimestamp(user_data["last_action"]["timestamp"], tz=datetime.timezone.utc),
        last_refresh=datetime.datetime.utcnow(),
        **user_data_kwargs,
    ).on_conflict(
        conflict_target=[User.tid],
        preserve=[
            User.name,
            User.level,
            User.discord_id,
            User.faction,
            User.status,
            User.last_action,
            User.last_refresh,
            *(getattr(User, k) for k in user_data_kwargs.keys()),
        ],
    ).execute()

    # Caches valid public personal stat keys
    try:
        n = rds().sadd("tornium:personal-stats", *(user_data["personal_stats"].keys()))

        if n > 0:
            rds().expire("tornium:personal-stats", 3600, nx=True)
    except KeyError:
        pass


@celery.shared_task(
    name="tasks.user.refresh_users",
    routing_key="default.refresh_users",
    queue="default",
    time_limit=5,
)
def refresh_users():
    user: User
    for user in User.select().where((User.key.is_null(False)) & (User.key != "")):
        tornget.signature(
            kwargs={
                "endpoint": "user/?selections=profile,discord,personalstats,battlestats",
                "key": user.key,
            },
            queue="api",
        ).apply_async(
            expires=300,
            link=update_user_self.s(),
            ignore_result=True,
        )


@celery.shared_task(
    name="tasks.user.fetch_attacks_user_runner",
    routing_key="quick.fetch_user_attacks",
    queue="quick",
    time_limit=5,
)
def fetch_attacks_user_runner():
    redis = rds()

    if (
        redis.exists("tornium:celery-lock:fetch-attacks-user")
        and redis.ttl("tornium:celery-lock:fetch-attacks-user") > 1
    ):  # Lock enabled
        logger.debug("Fetch attacks task terminated due to pre-existing task")
        raise Exception(
            f"Can not run task as task is already being run. Try again in "
            f"{redis.ttl('tornium:celery-lock:fetch-attacks-user')} seconds."
        )

    if redis.setnx("tornium:celery-lock:fetch-attacks-user", 1):
        redis.expire("tornium:celery-lock:fetch-attacks-user", 60)  # Lock for five minutes
    if redis.ttl("tornium:celery-lock:fetch-attacks-user") < 1:
        redis.expire("tornium:celery-lock:fetch-attacks-user", 1)

    user: User
    for user in User.select().where((User.key.is_null(False)) & (User.key != "")):
        if user.key in ("", None):
            continue
        elif user.faction_aa:
            continue
        elif user.last_attacks is None:
            User.update(last_attacks=datetime.datetime.utcnow()).where(User.tid == user.tid).execute()
            continue
        elif user.faction is not None and len(user.faction.aa_keys) > 0:
            continue

        tornget.signature(
            kwargs={
                "endpoint": "user/?selections=basic,attacks",
                "fromts": user.last_attacks.timestamp() + 1,  # Timestamp is inclusive,
                "key": user.key,
            },
            queue="api",
        ).apply_async(
            expires=300,
            link=stat_db_attacks_user.s(),
        )


@celery.shared_task(
    name="tasks.user.stat_db_attacks_user",
    routing_key="quick.stat_db_attacks_user",
    queue="quick",
    time_limit=5,
)
def stat_db_attacks_user(user_data):
    if len(user_data.get("attacks", [])) == 0:
        return

    try:
        user: User = User.select().where(User.tid == user_data["player_id"]).get()
    except DoesNotExist:
        return

    if (
        user.battlescore not in [None, 0]
        and user.battlescore_update is not None
        and user.battlescore_update.timestamp() - int(time.time()) <= 259200
    ):  # Three days
        user_score = user.battlescore
    else:
        return

    stats_data = []

    User.update(
        last_attacks=datetime.datetime.fromtimestamp(
            list(user_data["attacks"].values())[-1]["timestamp_ended"],
            tz=datetime.timezone.utc,
        ),
    ).where(User.tid == user.tid).execute()

    attack: dict
    for attack in user_data["attacks"].values():
        if attack["result"] in [
            "Assist",
            "Lost",
            "Stalemate",
            "Escape",
            "Looted",
            "Interrupted",
            "Timeout",
        ]:
            continue
        elif attack["defender_id"] in [
            4,
            10,
            15,
            17,
            19,
            20,
            21,
        ]:  # Checks if NPC fight (and you defeated NPC)
            continue
        elif attack["modifiers"]["fair_fight"] in (
            1,
            3,
        ):  # 3x FF can be greater than the defender battlescore indicated
            continue
        elif user.last_attacks is not None and attack["timestamp_ended"] <= user.last_attacks.timestamp():
            continue
        elif attack["respect"] == 0:
            continue

        # User: faction member
        # Opponent: non-faction member regardless of attack or defend
        if attack["attacker_id"] == user.tid:  # User is the attacker
            if attack["defender_faction"] != 0:
                Faction.insert(
                    tid=attack["defender_faction"],
                    name=attack["defender_factionname"],
                ).on_conflict(
                    conflict_target=[Faction.tid],
                    preserve=[Faction.name],
                ).execute()

            User.insert(
                tid=attack["defender_id"],
                name=attack["defender_name"],
                faction=attack["defender_faction"] if attack["defender_faction"] != 0 else None,
            ).on_conflict(
                conflict_target=[User.tid],
                preserve=[
                    User.name,
                    User.faction,
                ],
            ).execute()
            opponent_id = attack["defender_id"]
        else:  # User is the defender
            if attack["attacker_id"] in ("", 0):  # Attacker stealthed
                continue

            if attack["attacker_faction"] != 0:
                Faction.insert(tid=attack["attacker_faction"], name=attack["attacker_factionname"]).on_conflict(
                    conflict_target=[Faction.tid], preserve=[Faction.name]
                ).execute()

            User.insert(
                tid=attack["attacker_id"],
                name=attack["attacker_name"],
                faction=attack["attacker_faction"] if attack["attacker_faction"] != 0 else None,
            ).on_conflict(
                conflict_target=[User.tid],
                preserve=[
                    User.name,
                    User.faction,
                ],
            ).execute()
            opponent_id = attack["attacker_id"]

        try:
            update_user.delay(tid=opponent_id, key=user.key).forget()
        except Exception as e:
            logger.exception(e)
            continue

        try:
            if attack["defender_id"] == user.tid:
                opponent_score = user_score / ((attack["modifiers"]["fair_fight"] - 1) * 0.375)
            else:
                opponent_score = (attack["modifiers"]["fair_fight"] - 1) * 0.375 * user_score
        except DivisionByZero:
            continue

        if opponent_score == 0:
            continue

        stats_data.append(
            {
                "tid": opponent_id,
                "battlescore": int(opponent_score),
                "time_added": datetime.datetime.fromtimestamp(attack["timestamp_ended"]),
                "added_group": 0,
            }
        )

        try:
            Stat.create(
                tid=opponent_id,
                battlescore=int(opponent_score),
                time_added=datetime.datetime.fromtimestamp(attack["timestamp_ended"], tz=datetime.timezone.utc),
                added_group=0,
            )
        except Exception as e:
            logger.exception(e)
            continue
