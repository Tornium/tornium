# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
from decimal import DivisionByZero
import logging
import math
import random
import time

from honeybadger import honeybadger
from mongoengine.queryset.visitor import Q
import requests

from models.factiongroupmodel import FactionGroupModel
from models.factionmodel import FactionModel
from models.recruitmodel import RecruitModel
from models.servermodel import ServerModel
from models.statmodel import StatModel
from models.usermodel import UserModel
import redisdb
from tasks import celery_app, discordpost, logger, tornget, torn_stats_get
import utils
from utils.errors import RatelimitError, TornError

logger: logging.Logger


@celery_app.task
def refresh_factions():
    logger.debug("Started refresh_factions")
    requests_session = requests.Session()

    faction: FactionModel
    for faction in FactionModel.objects():
        logger.debug(f"Started refresh of faction {faction.tid}")
        aa_users = UserModel.objects(Q(factionaa=True) & Q(factionid=faction.tid))
        keys = []

        user: UserModel
        for user in aa_users:
            if user.key == "":
                logger.info(f"Removed AA from {user.tid} in refresh_factions")
                user.factionaa = False
                user.save()
                continue

            keys.append(user.key)

        keys = list(set(keys))
        faction.aa_keys = keys
        faction.save()

        if len(keys) == 0:
            continue

        try:
            faction_data = tornget(
                "faction/?selections=",
                key=random.choice(keys),
                session=requests_session,
            )
        except TornError as e:
            logger.exception(e)
            honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
            continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        if faction_data is None:
            continue

        faction = utils.first(FactionModel.objects(tid=faction.tid))
        faction.name = faction_data["name"]
        faction.respect = faction_data["respect"]
        faction.capacity = faction_data["capacity"]
        faction.leader = faction_data["leader"]
        faction.coleader = faction_data["co-leader"]
        faction.last_members = utils.now()

        keys = []

        leader = utils.first(UserModel.objects(tid=faction.leader))
        coleader = utils.first(UserModel.objects(tid=faction.coleader))

        if leader is not None and leader.key != "":
            keys.append(leader.key)
        if coleader is not None and coleader.key != "":
            keys.append(coleader.key)

        if len(keys) != 0:
            try:
                user_ts_data = torn_stats_get(
                    f"spy/faction/{faction.tid}", random.choice(keys)
                )
            except Exception as e:
                logger.exception(e)
                continue

            if not user_ts_data["status"]:
                continue

            for user_id, user_data in user_ts_data["faction"]["members"].items():
                if "spy" not in user_data:
                    continue

                user: UserModel = utils.first(UserModel.objects(tid=int(user_id)))

                if user is None:
                    continue
                elif user_data["spy"]["timestamp"] <= user.battlescore_update:
                    continue

                user.battlescore = (
                    math.sqrt(user_data["spy"]["strength"])
                    + math.sqrt(user_data["spy"]["defense"])
                    + math.sqrt(user_data["spy"]["speed"])
                    + math.sqrt(user_data["spy"]["dexterity"])
                )
                user.strength = user_data["spy"]["strength"]
                user.defense = user_data["spy"]["defense"]
                user.speed = user_data["spy"]["speed"]
                user.dexterity = user_data["spy"]["dexterity"]
                user.battlescore_update = user_data["spy"]["timestamp"]
                user.save()

        users = []

        for member_id, member in faction_data["members"].items():
            user = utils.first(UserModel.objects(tid=int(member_id)))
            users.append(int(member_id))

            if user is None:
                user = UserModel(
                    tid=int(member_id),
                    name=member["name"],
                    level=member["level"],
                    last_refresh=utils.now(),
                    admin=False,
                    key="",
                    battlescore=0,
                    battlescore_update=utils.now(),
                    discord_id=0,
                    servers=[],
                    factionid=faction.tid,
                    factionaa=False,
                    recruiter=False,
                    chain_hits=0,
                    status=member["last_action"]["status"],
                    last_action=member["last_action"]["timestamp"],
                    pro=False,
                    pro_expiration=0,
                )
                user.save()

            user.name = member["name"]
            user.level = member["level"]
            user.last_refresh = utils.now()
            user.factionid = faction.tid
            user.status = member["last_action"]["status"]
            user.last_action = member["last_action"]["timestamp"]
            user.save()

            recruit: RecruitModel = utils.last(
                RecruitModel.objects(Q(tid=user.tid) & Q(factionid=faction.tid))
            )

            if recruit is not None:
                recruit.tif = member["days_in_faction"]
                recruit.save()

        for user in UserModel.objects(factionid=faction.tid):
            if user.tid in users:
                continue

            user.factionid = 0
            user.factionaa = False
            user.save()

        if faction.chainconfig["od"] == 1 and len(keys) != 0:
            try:
                faction_od = tornget(
                    "faction/?selections=contributors",
                    stat="drugoverdoses",
                    key=random.choice(keys),
                    session=requests_session,
                )
            except TornError as e:
                logger.exception(e)
                honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
                continue
            except Exception as e:
                logger.exception(e)
                continue

            if len(faction.chainod) > 0:
                guild: ServerModel = utils.first(ServerModel.objects(sid=faction.guild))

                for tid, user_od in faction_od["contributors"]["drugoverdoses"].items():
                    if guild is None:
                        continue

                    try:
                        if user_od["contributed"] != faction.chainod.get(tid).get(
                            "contributed"
                        ):
                            overdosed_user = utils.first(UserModel.objects(tid=tid))
                            payload = {
                                "embeds": [
                                    {
                                        "title": "User Overdose",
                                        "description": f"User {tid if overdosed_user is None else overdosed_user.name} of "
                                        f"faction {faction.name} has overdosed.",
                                        "timestamp": datetime.datetime.utcnow().isoformat(),
                                        "footer": {"text": utils.torn_timestamp()},
                                        "components": [
                                            {
                                                "type": 1,
                                                "components": [
                                                    {
                                                        "type": 2,
                                                        "style": 5,
                                                        "label": "User",
                                                        "url": f"https://www.torn.com/profiles.php?XID={tid}",
                                                    }
                                                ],
                                            }
                                        ],
                                    }
                                ]
                            }

                            try:
                                discordpost.delay(
                                    f'channels/{faction.chainconfig["odchannel"]}/messages',
                                    payload=payload,
                                    dev=guild.skynet,
                                )
                            except Exception as e:
                                logger.exception(e)
                                honeybadger.notify(e)
                                continue
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        continue

            faction.chainod = faction_od["contributors"]["drugoverdoses"]

        faction.save()


@celery_app.task(time_limit=300)  # Prevents task for running for more than five minutes
def fetch_attacks():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    logger.debug("Fetch attacks task initiated")
    redis = redisdb.get_redis()

    if redis.exists("tornium:celery-lock:fetch-attacks"):  # Lock enabled
        logger.debug("Fetch attacks task terminated due to pre-existing task")
        raise Exception(
            f"Can not run task as task is already being run. Try again in {redis.ttl('tornium:celery-lock:fetch-attack')} seconds."
        )

    if redis.setnx("tornium:celery-lock:fetch-attacks", 1):
        redis.expire("tornium:celery-lock:fetch-attacks", 55)  # Lock for 55 seconds
    if redis.ttl("torniusm:celery-lock:fetch-attacks") < 0:
        redis.expire("tornium:celery-lock:fetch-attsacks", 1)

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

    faction: FactionModel
    for faction in FactionModel.objects():
        logger.debug(
            f"Starting fetch attacks task on faction {faction.name} [{faction.tid}]"
        )

        if faction.config["stats"] == 0:
            logger.debug(
                f"Skipping fetch attacks task on faction {faction.name} [{faction.tid}]"
            )
            continue

        if len(faction.aa_keys) == 0:
            aa_users = UserModel.objects(Q(factionaa=True) & Q(factionid=faction.tid))
            keys = []

            user: UserModel
            for user in aa_users:
                if user.key == "":
                    continue

                keys.append(user.key)

            keys = list(set(keys))

            if len(keys) == 0:
                continue
        else:
            keys = faction.aa_keys

        try:
            faction_data = tornget(
                "faction/?selections=basic,attacks",
                key=random.choice(keys),
                session=requests_session,
            )
        except TornError as e:
            logger.exception(e)
            honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
            continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        for attack in faction_data["attacks"].values():
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

            if attack["defender_faction"] == faction_data["ID"]:  # User is the defender
                if attack["attacker_id"] in ("", 0):
                    continue

                user = utils.first(UserModel.objects(tid=attack["defender_id"]))
                user_id = attack["defender_id"]

                opponent = utils.first(UserModel.objects(tid=attack["attacker_id"]))
                opponent_id = attack["attacker_id"]
            else:  # User is the attacker
                user = utils.first(UserModel.objects(tid=attack["attacker_id"]))
                user_id = attack["attacker_id"]

                opponent = utils.first(UserModel.objects(tid=attack["defender_id"]))
                opponent_id = attack["defender_id"]

            if user is None:
                try:
                    user_data = tornget(
                        f"user/{user_id}/?selections=profile,discord",
                        random.choice(keys),
                        session=requests_session,
                    )

                    user = UserModel(
                        tid=user_id,
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
                except TornError as e:
                    logger.exception(e)
                    honeybadger.notify(
                        e, context={"code": e.code, "endpoint": e.endpoint}
                    )
                    continue
                except Exception as e:
                    logger.exception(e)
                    continue

            if opponent is None:
                try:
                    user_data = tornget(
                        f"user/{opponent_id}/?selections=profile,discord",
                        random.choice(keys),
                        session=requests_session,
                    )

                    user = UserModel(
                        tid=opponent_id,
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
                except TornError as e:
                    logger.exception(e)
                    honeybadger.notify(
                        e, context={"code": e.code, "endpoint": e.endpoint}
                    )
                    continue
                except Exception as e:
                    logger.exception(e)
                    continue

            try:
                if user.battlescore_update - utils.now() <= 259200:  # Three days
                    user_score = user.battlescore
                else:
                    continue
            except IndexError:
                continue

            if user_score > 100000 or user_score == 0:
                continue
            elif attack["modifiers"]["fair_fight"] == 1:
                continue

            try:
                if attack["defender_faction"] == faction_data["ID"]:
                    opponent_score = user_score / (
                        (attack["modifiers"]["fair_fight"] - 1) * 0.375
                    )
                else:
                    opponent_score = (
                        (attack["modifiers"]["fair_fight"] - 1) * 0.375 * user_score
                    )
            except DivisionByZero:
                continue

            if opponent_score == 0:
                continue

            stat_faction: FactionModel = utils.first(
                FactionModel.objects(tid=user.factionid)
            )

            if stat_faction is None:
                globalstat = 1
                allowed_factions = []
            else:
                globalstat = stat_faction.statconfig["global"]
                allowed_factions = [stat_faction.tid]

                if str(stat_faction.tid) in faction_shares:
                    allowed_factions.extend(faction_shares[str(stat_faction.tid)])

                allowed_factions = list(set(allowed_factions))

            stat_entry = StatModel(
                statid=utils.last(StatModel.objects()).statid + 1
                if StatModel.objects().count() != 0
                else 0,
                tid=opponent_id,
                battlescore=opponent_score,
                timeadded=attack["timestamp_ended"],
                addedid=user_id,
                addedfactiontid=user.factionid,
                globalstat=globalstat,
                allowedfactions=allowed_factions,
            )
            stat_entry.save()
