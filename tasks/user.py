# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import math
import time

from honeybadger import honeybadger
from models.recruitmodel import RecruitModel
from mongoengine.queryset.visitor import Q
import requests

from models.factionmodel import FactionModel
from models.factiongroupmodel import FactionGroupModel
from models.statmodel import StatModel
from models.usermodel import UserModel
from tasks import celery_app, logger, tornget
import utils


@celery_app.task
def update_user(tid: int, key: str, refresh_existing=True):
    if key in ("", None):
        return utils.MissingKeyError

    user: UserModel = utils.first(UserModel.objects(tid=tid))

    if user is not None and not refresh_existing:
        return

    if user is not None and user.key not in (None, ""):
        user_data = tornget(f"user/{tid}/?selections=profile,discord", user.key)
    else:
        user_data = tornget(f"user/{tid}/?selections=profile,discord", key)

    if user_data["player_id"] != tid:
        raise Exception("TID does not match returned player_ID")

    if user is None:
        user: UserModel = UserModel(
            tid=user_data["player_id"],
            name=user_data["name"],
            level=user_data["level"],
            admin=False,
            key="",
            battlescore=0,
            battlescore_update=utils.now(),
            discord_id=user_data["discord"]["discordID"]
            if user_data["discord"]["discordID"] != ""
            else 0,
            servers=[],
            factionid=user_data["faction"]["faction_id"],
            factionaa=False,
            recruiter=False,
            last_refresh=utils.now(),
            chain_hits=0,
            status=user_data["last_action"]["status"],
            last_action=user_data["last_action"]["timestamp"],
            pro=False,
            pro_expiration=0,
        )
        user.save()
    else:
        user.name = user_data["name"]
        user.level = user_data["level"]
        user.discord_id = (
            user_data["discord"]["discordID"]
            if user_data["discord"]["discordID"] != ""
            else 0
        )

        try:
            user.factionid = user_data["faction"]["faction_id"]
        except KeyError:
            logger.error(
                f"User {user_data['name']} [{user_data['player_id']}] has missing faction."
            )
            logger.info(user_data)

        user.last_refresh = utils.now()
        user.status = user_data["last_action"]["status"]
        user.last_action = user_data["last_action"]["timestamp"]
        user.save()

    faction: FactionModel = utils.first(
        FactionModel.objects(tid=user_data["faction"]["faction_id"])
    )

    if faction is None:
        faction: FactionModel = FactionModel(
            tid=user_data["faction"]["faction_id"],
            name=user_data["faction"]["faction_name"],
        )
        faction.save()


@celery_app.task
def refresh_users():
    requests_session = requests.Session()

    user: UserModel
    for user in UserModel.objects(key__ne=""):
        if user.key == "":
            continue

        try:
            user_data = tornget(
                f"user/?selections=profile,battlestats,discord",
                user.key,
                session=requests_session,
            )
        except utils.TornError as e:
            logger.exception(e)
            honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
            continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        try:  # Torn API debug
            user.factionid = user_data["faction"]["faction_id"]
        except KeyError:
            logger.error(
                f"User {user_data['name']} [{user_data['player_id']}] has missing faction."
            )
            logger.info(user_data)

        user.name = user_data["name"]
        user.last_refresh = utils.now()
        user.status = user_data["last_action"]["status"]
        user.last_action = user_data["last_action"]["timestamp"]
        user.level = user_data["level"]
        user.discord_id = (
            user_data["discord"]["discordID"]
            if user_data["discord"]["discordID"] != ""
            else 0
        )
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

        if user.factionid != 0:
            faction: FactionModel = utils.first(
                FactionModel.objects(tid=user.factionid)
            )

            if faction is None:
                faction = FactionModel(
                    tid=user.factionid, name=user_data["faction"]["faction_name"]
                )
                faction.save()

            try:
                tornget(
                    f"faction/?selections=positions", user.key, session=requests_session
                )
            except utils.TornError as e:
                if e.code != 7:
                    logger.exception(e)
                    honeybadger.notify(
                        e, context={"code": e.code, "endpoint": e.endpoint}
                    )
                    continue
                else:
                    if user.factionaa:
                        user.factionaa = False
                        user.save()

                    continue
            except Exception as e:
                logger.exception(e)
                honeybadger.notify(e)

                if user.factionaa:
                    user.factionaa = False
                    user.save()

                continue

            user.factionaa = True
            user.save()
        else:
            user.factionaa = False
            user.save()


@celery_app.task
def mail_check():
    requests_session = requests.Session()

    user: UserModel
    for user in UserModel.objects(Q(key__ne="") & Q(pro=1)):
        if user.key == "" or not user.pro:
            continue

        try:
            mail_data = tornget(
                f"user/?selections=messages",
                user.key,
                session=requests_session,
                fromts=user.recruit_mail_update,
            )
        except utils.TornError as e:
            logger.exception(e)
            honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
            continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        for mailid, mail in mail_data.items():
            if mail["type"] != "User message":
                continue
            elif user.recruiter_code not in mail["title"]:
                continue

            recruit: RecruitModel = utils.last(
                RecruitModel.objects(Q(tid=mail["ID"]) & Q(recruiter=user.tid))
            )

            if recruit is None:
                continue
            if recruit.status == 2:
                continue

            recruit.messages_received += 1
            recruit.save()

        user.recruit_mail_update = utils.now()
        user.save()


@celery_app.task
def fetch_attacks_users():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    requests_session = requests.Session()

    try:
        last_timestamp = utils.last(StatModel.objects()).timeadded
    except AttributeError:
        last_timestamp = 0

    faction_shares = {}

    group: FactionGroupModel
    for group in FactionGroupModel.objects():
        for member in group.sharestats:
            if str(member) in faction_shares:
                faction_shares[str(member)].extend(group.members)
            else:
                faction_shares[str(member)] = group.members

    for factiontid, shares in faction_shares.items():
        faction_shares[factiontid] = list(set(shares))

    user: UserModel
    for user in UserModel.objects(Q(key__ne="") & Q(factionid__ne=0)):
        if user.key == "":
            continue
        elif user.factionid == 0:
            continue

        faction: FactionModel = utils.first(FactionModel.objects(tid=user.factionid))

        if faction is not None and time.time() - faction.last_members > 3600:
            continue
        elif faction is not None and faction.config["stats"] == 1:
            continue

        try:
            user_data = tornget(
                "user/?selections=basic,attacks", key=user.key, session=requests_session
            )
        except utils.TornError as e:
            logger.exception(e)
            honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
            continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        for attack in user_data["attacks"].values():
            # if attack["defender_faction"] == user.factionid and user.factionid != 0:
            #     continue
            if attack["result"] in ["Assist", "Lost", "Stalemate", "Escape"]:
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
            elif (
                attack["modifiers"]["fair_fight"] == 3
            ):  # 3x FF can be greater than the defender battlescore indicated
                continue
            elif attack["timestamp_ended"] < last_timestamp:
                continue

            try:
                if user.battlescore_update - utils.now() <= 10800000:  # Three hours
                    user_score = user.battlescore
                else:
                    continue
            except IndexError:
                continue

            if user_score > 100000:
                continue

            if attack["defender_id"] == user.tid:
                opponent_score = user_score / (
                    (attack["modifiers"]["fair_fight"] - 1) * 0.375
                )
            else:
                opponent_score = (
                    (attack["modifiers"]["fair_fight"] - 1) * 0.375 * user_score
                )

            if opponent_score == 0:
                continue

            if faction is None:
                globalstat = 1
                allowed_factions = [user.factionid]
            else:
                globalstat = faction.statconfig["global"]
                allowed_factions = [faction.tid]

                if str(faction.tid) in faction_shares:
                    allowed_factions.extend(faction_shares[str(faction.tid)])

                allowed_factions = list(set(allowed_factions))

            stat_entry = StatModel(
                statid=utils.last(StatModel.objects()).statid + 1
                if StatModel.objects().count() != 0
                else 0,
                tid=attack["defender_id"]
                if attack["defender_id"] == user.tid
                else attack["attacker_id"],
                battlescore=opponent_score,
                timeadded=attack["timestamp_ended"],
                addedid=attack["attacker_id"]
                if attack["defender_id"] == user.tid
                else attack["defender_id"],
                addedfactiontid=user.factionid,
                globalstat=globalstat,
                allowedfactions=allowed_factions,
            )
            stat_entry.save()

            opponent = utils.first(UserModel.objects(tid=stat_entry.tid))

            if opponent is None:
                try:
                    user_data = tornget(
                        f"user/{stat_entry.tid}/?selections=profile,discord",
                        user.key,
                        session=requests_session,
                    )

                    user = UserModel(
                        tid=stat_entry.tid,
                        name=user_data["name"],
                        level=user_data["level"],
                        admin=False,
                        key="",
                        battlescore=0,
                        battlescore_update=utils.now(),
                        discord_id=user_data["discord"]["discordID"]
                        if user_data["discord"]["discordID"] != ""
                        else 0,
                        servers=[],
                        factionid=user_data["faction"]["faction_id"],
                        factionaa=False,
                        recruiter=False,
                        last_refresh=utils.now(),
                        chain_hits=0,
                        status=user_data["last_action"]["status"],
                        last_action=user_data["last_action"]["timestamp"],
                        pro=False,
                        pro_expiration=0,
                    )
                    user.save()
                except utils.TornError as e:
                    logger.exception(e)
                    honeybadger.notify(
                        e, context={"code": e.code, "endpoint": e.endpoint}
                    )
                    continue
                except Exception as e:
                    logger.exception(e)
                    continue
