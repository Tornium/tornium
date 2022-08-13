# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
from decimal import DivisionByZero
import logging
import math
import random

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
from utils.errors import TornError

logger: logging.Logger


@celery_app.task
def refresh_factions():
    requests_session = requests.Session()

    faction: FactionModel
    for faction in FactionModel.objects():
        aa_users = UserModel.objects(Q(factionaa=True) & Q(factionid=faction.tid))
        keys = []

        user: UserModel
        for user in aa_users:
            if user.key == "":
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

        faction = FactionModel.objects(tid=faction.tid).first()
        faction.name = faction_data["name"]
        faction.respect = faction_data["respect"]
        faction.capacity = faction_data["capacity"]
        faction.leader = faction_data["leader"]
        faction.coleader = faction_data["co-leader"]
        faction.last_members = utils.now()

        keys = []

        leader = UserModel.objects(tid=faction.leader).first()
        coleader = UserModel.objects(tid=faction.coleader).first()

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

                user: UserModel = UserModel.objects(tid=int(user_id)).first()

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
            user = UserModel.objects(tid=int(member_id)).first()
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

            recruit: RecruitModel = (
                RecruitModel.objects(Q(tid=user.tid) & Q(factionid=faction.tid))
                .order_by("-id")
                .first()
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
                guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

                for tid, user_od in faction_od["contributors"]["drugoverdoses"].items():
                    if guild is None:
                        continue

                    try:
                        if user_od["contributed"] != faction.chainod.get(tid).get(
                            "contributed"
                        ):
                            overdosed_user = UserModel.objects(tid=tid).first()
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


@celery_app.task(time_limit=600)  # Prevents task for running for more than ten minutes
# @celery_app.task
def fetch_attacks():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    logger.debug("Fetch attacks task initiated")
    redis = redisdb.get_redis()

    if redis.exists("tornium:celery-lock:fetch-attacks"):  # Lock enabled
        logger.debug("Fetch attacks task terminated due to pre-existing task")
        raise Exception(
            f"Can not run task as task is already being run. Try again in {redis.ttl('tornium:celery-lock:fetch-attack')} seconds."
        )

    if redis.setnx("tornium:celery-lock:fetch-attacks", 1):
        redis.expire("tornium:celery-lock:fetch-attacks", 300)  # Lock for five minutes
    if redis.ttl("torniusm:celery-lock:fetch-attacks") < 0:
        redis.expire("tornium:celery-lock:fetch-attacks", 1)

    requests_session = requests.Session()
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
    for faction in FactionModel.objects(
        Q(aa_keys__not__size=0) & Q(aa_keys__exists=True)
    ):
        logger.debug(
            f"Starting fetch attacks task on faction {faction.name} [{faction.tid}]"
        )

        if len(faction.aa_keys) == 0:
            continue
        if faction.config["stats"] == 0:
            # logger.debug(
            #     f"Skipping fetch attacks task on faction {faction.name} [{faction.tid}]"
            # )
            continue

        if faction.last_attacks == 0:
            faction.last_attacks = utils.now()
            faction.save()
            continue

        try:
            faction_data = tornget(
                "faction/?selections=basic,attacks",
                fromts=faction.last_attacks + 1,  # Timestamp is inclusive
                key=random.choice(faction.aa_keys),
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

        logger.debug(
            f"Faction refresh running on faction {faction.name} [{faction.tid}] with {len(faction_data['attacks'])} "
            f"attacks"
        )

        attack_status = {
            "success": 0,
            "skipped": {
                "total": 0,
                "NPC": 0,
                "result": 0,
                "ff": 0,
                "timestamp": 0,
                "stealth": 0,
                "battlescore": 0,
                "battleupdate": 0,
                "misc": 0,
            },
        }

        for attack in faction_data["attacks"].values():
            logger.debug(f"START attack {attack['code']}")

            if attack["result"] in ["Assist", "Lost", "Stalemate", "Escape"]:
                # logger.debug(
                #     f"SKIP attack {attack['code']} (result: {attack['result']})"
                # )
                attack_status["skipped"]["result"] += 1
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
                # logger.debug(f"SKIP attack {attack['code']} (NPC)")
                attack_status["skipped"]["NPC"] += 1
                continue
            elif attack["modifiers"]["fair_fight"] in (
                1,
                3,
            ):  # 3x FF can be greater than the defender battlescore indicated
                # logger.debug(f"SKIP attack {attack['code']} (FF)")
                attack_status["skipped"]["ff"] += 1
                continue
            elif attack["timestamp_ended"] <= faction.last_attacks:
                # logger.debug(f"SKIP attack {attack['code']} (timestamp_ended)")
                attack_status["skipped"]["timestamp"] += 1
                continue

            # User: faction member
            # Opponent: non-faction member regardless of attack or defend

            logger.debug(f"GET user and opponent of attack {attack['code']}")

            if (
                attack["defender_faction"] == faction_data["ID"]
            ):  # Defender fac is the fac making the call
                # logger.debug(f"INFO attack {attack['code']} (defend)")

                if attack["attacker_id"] in ("", 0):  # Attacker stealthed
                    # logger.debug(f"SKIP attack {attack['code']} (stealth)")
                    attack_status["skipped"]["stealth"] += 1
                    continue
                elif attack["respect"] == 0:  # Attack on fac member
                    # logger.debug(f"SKIP attack {attack['code']} (fac mem)")
                    attack_status["skipped"]["misc"] += 1
                    continue

                user: UserModel = UserModel.objects(tid=attack["defender_id"]).first()
                user_id = attack["defender_id"]

                if user is None:
                    attack_status["skipped"]["misc"] += 1
                    continue

                try:
                    if user.battlescore_update - utils.now() <= 259200:  # Three days
                        user_score = user.battlescore
                    else:
                        attack_status["skipped"]["battleupdate"] += 1
                        continue
                except IndexError:
                    # logger.debug(f"EXCEPTION attack {attack['code']} (IndexError)")
                    attack_status["skipped"]["misc"] += 1
                    continue
                except AttributeError as e:
                    logger.exception(e)
                    honeybadger.notify(e)
                    continue

                # TODO: Update
                if user_score > 100000 or user_score == 0:  # 100k old value
                    # logger.debug(f"SKIP attack {attack['code']} (invalid user score)")
                    attack_status["skipped"]["battlescore"] += 1
                    continue

                opponent: UserModel = UserModel.objects(
                    tid=attack["attacker_id"]
                ).first()
                opponent_id = attack["attacker_id"]

                if opponent is None:
                    opponent = UserModel(
                        tid=attack["attacker_id"],
                        name=attack["attacker_name"],
                        factionid=attack["attacker_faction"],
                    )
                    opponent.save()
            else:  # User is the attacker
                # logger.debug(f"INFO attack {attack['code']} (attack)")

                user: UserModel = UserModel.objects(tid=attack["attacker_id"]).first()
                user_id = attack["attacker_id"]

                if user is None:
                    attack_status["skipped"]["misc"] += 1
                    continue

                try:
                    if user.battlescore_update - utils.now() <= 259200:  # Three days
                        user_score = user.battlescore
                    else:
                        attack_status["skipped"]["battleupdate"] += 1
                        continue
                except IndexError:
                    # logger.debug(f"EXCEPTION attack {attack['code']} (IndexError)")
                    attack_status["skipped"]["misc"] += 1
                    continue
                except AttributeError as e:
                    logger.exception(e)
                    honeybadger.notify(e)
                    continue

                # TODO: Update
                if user_score > 100000 or user_score == 0:  # 100k old value
                    # logger.debug(f"SKIP attack {attack['code']} (invalid user score)")
                    attack_status["skipped"]["battlescore"] += 1
                    continue

                opponent: UserModel = UserModel.objects(
                    tid=attack["defender_id"]
                ).first()
                opponent_id = attack["defender_id"]

                if opponent is None:
                    opponent = UserModel(
                        tid=attack["attacker_id"],
                        name=attack["attacker_name"],
                        factionid=attack["attacker_faction"],
                    )
                    opponent.save()

            # if opponent is None:
            #     try:
            #         update_user.delay(tid=opponent_id, key=random.choice(keys))
            #     except TornError as e:
            #         logger.exception(e)
            #         honeybadger.notify(
            #             e, context={"code": e.code, "endpoint": e.endpoint}
            #         )
            #         continue
            #     except Exception as e:
            #         logger.exception(e)
            #         continue

            logger.debug(f"GET stat scores of attack {attack['code']}")

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
                # logger.debug(f"EXCEPTION attack {attack['code']} (DivisionByZero)")
                attack_status["skipped"]["misc"] += 1
                continue

            if opponent_score == 0:
                # logger.debug(f"SKIP attack {attack['code']} (zero opponent score)")
                attack_status["skipped"]["misc"] += 1
                continue

            stat_faction: FactionModel = FactionModel.objects(
                tid=user.factionid
            ).first()

            if stat_faction is None or user.factionid == 0:
                globalstat = 1
                allowed_factions = []
            else:
                globalstat = stat_faction.statconfig["global"]
                allowed_factions = [stat_faction.tid]

                if str(stat_faction.tid) in faction_shares:
                    allowed_factions.extend(faction_shares[str(stat_faction.tid)])

                allowed_factions = list(set(allowed_factions))

            logger.debug(f"SET stat entry of attack {attack['code']}")

            try:
                stat_entry = StatModel(
                    statid=StatModel.objects().order_by("-id").first()
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
            except Exception as e:
                logger.exception(e)
                honeybadger.notify(e)
                continue

            attack_status["success"] += 1

            logger.debug(f"SUCCESS attack {attack['code']}")

        if len(faction_data["attacks"].values()) > 0:
            try:
                faction.last_attacks = list(faction_data["attacks"].values())[-1][
                    "timestamp_ended"
                ]
                faction.save()
            except Exception as e:
                logger.exception(e)

        logger.debug(attack_status)
        logger.debug(
            f"Fetch attacks task has completed on faction {faction.name} [{faction.tid}]"
        )
