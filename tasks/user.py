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
import typing
from decimal import DivisionByZero

import mongoengine.errors
import requests

import redisdb
import utils
from models.attackmodel import AttackModel
from models.factionmodel import FactionModel
from models.personalstatmodel import PersonalStatModel
from models.statmodel import StatModel
from models.usermodel import UserModel
from tasks import celery_app, logger, tornget

ATTACK_RESULTS = {
    "Lost": 0,
    "Attacked": 1,
    "Mugged": 2,
    "Hospitalized": 3,
    "Stalemate": 4,
    "Escape": 5,
    "Assist": 6,
    "Special": 7,
    "Looted": 8,
    "Arrested": 9,
    "Timeout": 10,
    "Interrupted": 11,
}


@celery_app.task
def update_user(key: str, tid: int = 0, discordid: int = 0, refresh_existing=True):
    if key is None or key == "":
        raise utils.MissingKeyError
    elif (tid == 0 and discordid == 0) or (tid != 0 and discordid != 0):
        raise Exception("No valid user ID passed")

    if tid != 0:
        user: UserModel = UserModel.objects(tid=tid).first()
    else:
        user: UserModel = UserModel.objects(discord_id=discordid).first()

    if user is not None and not refresh_existing:
        return user, {"refresh": False}

    if user is not None and user.key not in (None, ""):
        user_data = tornget(f"user/{tid}/?selections=profile,discord,personalstats", user.key)
    else:
        user_data = tornget(f"user/{tid}/?selections=profile,discord,personalstats", key)

    if int(user_data["player_id"]) != int(tid) and tid != 0:
        raise Exception("TID does not match returned player_ID")
    elif (
        discordid not in ("", 0)
        and user_data["discord"]["discordID"] not in ("", 0)
        and int(user_data["discord"]["discordID"]) != int(discordid)
    ):
        raise Exception("discordid does not match returned discordID")

    if user is None:
        user: UserModel = UserModel.objects(tid=user_data["player_id"]).modify(
            upsert=True,
            new=True,
            set__name=user_data["name"],
            set__level=user_data["level"],
            set__discord_id=user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0,
            set__factionid=user_data["faction"]["faction_id"],
            set__status=user_data["last_action"]["status"],
            set__last_action=user_data["last_action"]["timestamp"],
        )
    else:
        user.name = user_data["name"]
        user.level = user_data["level"]
        user.discord_id = user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0

        try:
            user.factionid = user_data["faction"]["faction_id"]
        except KeyError:
            logger.error(f"User {user_data['name']} [{user_data['player_id']}] has missing faction.")
            logger.info(user_data)

        user.last_refresh = utils.now()
        user.status = user_data["last_action"]["status"]
        user.last_action = user_data["last_action"]["timestamp"]
        user.save()

    faction: FactionModel = FactionModel.objects(tid=user_data["faction"]["faction_id"]).first()

    if faction is None:
        faction: FactionModel = FactionModel(
            tid=user_data["faction"]["faction_id"],
            name=user_data["faction"]["faction_name"],
        )
        faction.save()
    elif faction.name != user_data["faction"]["faction_name"]:
        faction.name = user_data["faction"]["faction_name"]
        faction.save()

    now = datetime.datetime.utcnow()
    now = int(
        datetime.datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=0,
            second=0,
        )
        .replace(tzinfo=datetime.timezone.utc)
        .timestamp()
    )

    try:
        PersonalStatModel(
            **dict(
                {"pstat_id": int(bin(user.tid << 8), 2) + int(bin(now), 2), "tid": user.tid, "timestamp": utils.now()},
                **user_data["personalstats"],
            )
        ).save()
    except mongoengine.errors.OperationError:
        pass
    except Exception as e:
        logger.exception(e)

    return user_data


@celery_app.task
def refresh_users():
    requests_session = requests.Session()

    user: UserModel
    for user in UserModel.objects(key__nin=[None, ""]):
        if user.key == "":
            continue

        try:
            user_data = tornget(
                "user/?selections=profile,battlestats,discord",
                user.key,
                session=requests_session,
            )
        except utils.TornError as e:
            if e.code in (2, 13):
                user.key = ""
                user.save()
                continue

            continue
        except Exception:
            continue

        try:  # Torn API debug
            user.factionid = user_data["faction"]["faction_id"]
        except KeyError:
            logger.error(f"User {user_data['name']} [{user_data['player_id']}] has missing faction.")
            logger.info(user_data)

        user.name = user_data["name"]
        user.last_refresh = utils.now()
        user.status = user_data["last_action"]["status"]
        user.last_action = user_data["last_action"]["timestamp"]
        user.level = user_data["level"]
        user.discord_id = user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0
        user.strength = user_data["strength"]
        user.defense = user_data["defense"]
        user.speed = user_data["speed"]
        user.dexterity = user_data["dexterity"]

        battlescore = (
            math.sqrt(user_data["strength"])
            + math.sqrt(user_data["defense"])
            + math.sqrt(user_data["speed"])
            + math.sqrt(user_data["dexterity"])
        )
        user.battlescore = battlescore
        user.battlescore_update = utils.now()
        user.save()


@celery_app.task
def fetch_attacks_user_runner():
    redis = redisdb.get_redis()

    if (
        redis.exists("tornium:celery-lock:fetch-attacks-user")
        and redis.ttl("tornium:celery-lock:fetch-attacks-user") < 1
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

    user: UserModel
    for user in UserModel.objects(key__nin=[None, ""]):
        if user.key in (None, ""):
            continue
        elif user.factionaa:
            continue
        if user.last_attacks == 0:
            user.last_attacks = utils.now()
            user.save()
            continue

        if user.factionid != 0:
            faction: typing.Optional[FactionModel] = FactionModel.objects(tid=user.factionid).first()

            if faction is not None and len(faction.aa_keys) > 0:
                continue

        tornget.s(
            "user/?selections=basic,attacks",
            fromts=user.last_attacks + 1,  # Timestamp is inclusive,
            key=user.key,
        ).apply_async(
            expires=300,
            link=stat_db_attacks_user.s(),
        )


@celery_app.task
def stat_db_attacks_user(user_data):
    if "attacks" not in user_data:
        return
    elif len(user_data["attacks"]) == 0:
        return

    user: typing.Optional[UserModel] = UserModel.objects(tid=user_data["player_id"]).first()

    if user is None:
        return

    attacks_data = []
    stats_data = []

    attack: dict
    for attack in user_data["attacks"].values():
        attacks_data.append(
            {
                "code": attack.get("code"),
                "timestamp_started": attack.get("timestamp_started"),
                "timestamp_ended": attack.get("timestamp_ended"),
                "attacker": attack.get("attacker_id"),
                "attacker_faction": attack.get("attacker_faction"),
                "defender": attack.get("defender_id"),
                "defender_faction": attack.get("defender_faction"),
                "result": ATTACK_RESULTS.get(attack.get("result"), -1),
                "stealth": attack.get("stealthed"),
                "respect": attack.get("respect"),
                "chain": attack.get("chain"),
                "raid": attack.get("raid"),
                "ranked_war": attack.get("ranked_war"),
                "modifiers": attack.get("modifiers"),
            }
        )

        if attack["result"] in ["Assist", "Lost", "Stalemate", "Escape", "Looted", "Interrupted", "Timeout"]:
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
        elif attack["timestamp_ended"] <= user.last_attacks:
            continue
        elif attack["respect"] == 0:
            continue
        elif user is None:
            continue

        try:
            if user.battlescore_update - utils.now() <= 259200:  # Three days
                user_score = user.battlescore
            else:
                continue
        except IndexError:
            continue
        except AttributeError as e:
            logger.exception(e)
            continue

        if user_score == 0:
            continue

        # User: faction member
        # Opponent: non-faction member regardless of attack or defend

        if attack["attacker_id"] == user.tid:  # Attacker is user
            opponent: typing.Optional[UserModel] = UserModel.objects(tid=attack["defender_id"]).first()
            opponent_id = attack["defender_id"]

            if opponent is None:
                opponent = UserModel.objects(tid=attack["defender_id"]).modify(
                    upsert=True,
                    new=True,
                    set__name=attack["defender_name"],
                    set__factionid=attack["defender_faction"],
                )
        else:  # Defender is user
            if attack["attacker_id"] in ("", 0):  # Attacker stealthed
                continue

            opponent: typing.Optional[UserModel] = UserModel.objects(tid=attack["attacker_id"]).first()
            opponent_id = attack["attacker_id"]

            if opponent is None:
                opponent = UserModel.objects(tid=attack["attacker_id"]).modify(
                    upsert=True,
                    new=True,
                    set__name=attack["attacker_name"],
                    set__factionid=attack["attacker_faction"],
                )

        try:
            update_user.delay(tid=opponent_id, key=user.key)
        except (utils.TornError, utils.NetworkingError):
            continue
        except Exception as e:
            logger.exception(e)
            continue

        try:
            if attack["attacker_id"] == user.tid:
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
                "battlescore": opponent_score,
                "timeadded": attack["timestamp_ended"],
                "addedid": user.tid,
                "addedfactiontid": user.factionid,
                "globalstat": True,
            }
        )

    # Resolves duplicate keys: https://github.com/MongoEngine/mongoengine/issues/1465#issuecomment-445443894
    try:
        attacks_data = [AttackModel(**attack).to_mongo() for attack in attacks_data]
        AttackModel._get_collection().insert_many(attacks_data, ordered=False)
    except mongoengine.errors.BulkWriteError:
        logger.warning(
            f"Attack data (from user TID {user.tid}) bulk insert failed. Duplicates may have been found and "
            f"were skipped."
        )

    try:
        if len(stats_data) > 0:
            stats_data = [StatModel(**stats).to_mongo() for stats in stats_data]
            StatModel._get_collection().insert_many(stats_data, ordered=False)
    except mongoengine.errors.BulkWriteError:
        logger.warning(
            f"Stats data (from user TID {user.tid}) bulk insert failed. Duplicates may have been found and "
            f"were skipped."
        )

    user.last_attacks = list(user_data["attacks"].values())[-1]["timestamp_ended"]
    user.save()
