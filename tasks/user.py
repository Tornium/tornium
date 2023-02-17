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

import mongoengine.errors
import requests

import utils
from models.factionmodel import FactionModel
from models.personalstatmodel import PersonalStatModel
from models.usermodel import UserModel
from tasks import celery_app, logger, tornget


@celery_app.task
def update_user(key: str, tid: int = 0, discordid: int = 0, refresh_existing=True):
    if key in ("", None):
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
    elif int(user_data["discord"]["discordID"]) != int(discordid) and discordid != 0:
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


# @celery_app.task
# def fetch_attacks_users():
#     # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
#     requests_session = requests.Session()
#
#     try:
#         last_timestamp = StatModel.objects().order_by("-statid").first().timeadded
#     except AttributeError:
#         last_timestamp = 0
#
#     faction_shares = {}
#
#     group: FactionGroupModel
#     for group in FactionGroupModel.objects():
#         for member in group.sharestats:
#             if str(member) in faction_shares:
#                 faction_shares[str(member)].extend(group.members)
#             else:
#                 faction_shares[str(member)] = group.members
#
#     for factiontid, shares in faction_shares.items():
#         faction_shares[factiontid] = list(set(shares))
#
#     user: UserModel
#     for user in UserModel.objects(Q(key__nin=[None, ""]) & Q(factionid__ne=0)):
#         if user.key == "":
#             continue
#         elif user.factionid == 0:
#             continue
#
#         faction: FactionModel = FactionModel.objects(tid=user.factionid).first()
#
#         if faction is not None and time.time() - faction.last_members > 3600:
#             continue
#         elif faction is not None and faction.config["stats"] == 1:
#             continue
#
#         try:
#             user_data = tornget(
#                 "user/?selections=basic,attacks", key=user.key, session=requests_session
#             )
#         except utils.TornError as e:
#             logger.exception(e)
#             continue
#         except Exception as e:
#             logger.exception(e)
#             continue
#
#         for attack in user_data["attacks"].values():
#             # if attack["defender_faction"] == user.factionid and user.factionid != 0:
#             #     continue
#             if attack["result"] in ["Assist", "Lost", "Stalemate", "Escape"]:
#                 continue
#             elif attack["defender_id"] in [
#                 4,
#                 10,
#                 15,
#                 17,
#                 19,
#                 20,
#                 21,
#             ]:  # Checks if NPC fight (and you defeated NPC)
#                 continue
#             elif (
#                 attack["modifiers"]["fair_fight"] == 3
#             ):  # 3x FF can be greater than the defender battlescore indicated
#                 continue
#             elif attack["timestamp_ended"] < last_timestamp:
#                 continue
#
#             try:
#                 if user.battlescore_update - utils.now() <= 10800000:  # Three hours
#                     user_score = user.battlescore
#                 else:
#                     continue
#             except IndexError:
#                 continue
#
#             if user_score > 100000:
#                 continue
#
#             if attack["defender_id"] == user.tid:
#                 opponent_score = user_score / (
#                     (attack["modifiers"]["fair_fight"] - 1) * 0.375
#                 )
#             else:
#                 opponent_score = (
#                     (attack["modifiers"]["fair_fight"] - 1) * 0.375 * user_score
#                 )
#
#             if opponent_score == 0:
#                 continue
#
#             if faction is None:
#                 globalstat = 1
#                 allowed_factions = [user.factionid]
#             else:
#                 globalstat = faction.statconfig["global"]
#                 allowed_factions = [faction.tid]
#
#                 if str(faction.tid) in faction_shares:
#                     allowed_factions.extend(faction_shares[str(faction.tid)])
#
#                 allowed_factions = list(set(allowed_factions))
#
#             stat_entry = StatModel(
#                 statid=StatModel.objects().order_by("-statid").first().statid + 1
#                 if StatModel.objects().count() != 0
#                 else 0,
#                 tid=attack["defender_id"]
#                 if attack["defender_id"] == user.tid
#                 else attack["attacker_id"],
#                 battlescore=opponent_score,
#                 timeadded=attack["timestamp_ended"],
#                 addedid=attack["attacker_id"]
#                 if attack["defender_id"] == user.tid
#                 else attack["defender_id"],
#                 addedfactiontid=user.factionid,
#                 globalstat=globalstat,
#             )
#             stat_entry.save()
#
#             opponent = UserModel.objects(tid=stat_entry.tid).first()
#
#             if opponent is None:
#                 try:
#                     user_data = tornget(
#                         f"user/{stat_entry.tid}/?selections=profile,discord",
#                         user.key,
#                         session=requests_session,
#                     )
#
#                     user = UserModel(
#                         tid=stat_entry.tid,
#                         name=user_data["name"],
#                         level=user_data["level"],
#                         discord_id=user_data["discord"]["discordID"]
#                         if user_data["discord"]["discordID"] != ""
#                         else 0,
#                         factionid=user_data["faction"]["faction_id"],
#                         status=user_data["last_action"]["status"],
#                         last_action=user_data["last_action"]["timestamp"],
#                     )
#                     user.save()
#                 except utils.TornError as e:
#                     logger.exception(e)
#                     continue
#                 except Exception as e:
#                     logger.exception(e)
#                     continue
