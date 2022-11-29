# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
from decimal import DivisionByZero
import logging
import math
import random
import uuid

from honeybadger import honeybadger
from mongoengine.queryset.visitor import Q
import requests

from models.factionmodel import FactionModel
from models.positionmodel import PositionModel
from models.recruitmodel import RecruitModel
from models.servermodel import ServerModel
from models.statmodel import StatModel
from models.usermodel import UserModel
import redisdb
from tasks import celery_app, discordpost, logger, tornget, torn_stats_get
from tasks.user import update_user
import utils
from utils.errors import NetworkingError, TornError

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
                "faction/?selections=basic,positions",
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

        positions = PositionModel.objects(factiontid=faction.tid)
        positions_names = [position.name for position in positions]
        positions_data = {
            "Recruit": {
                "uuid": None,
                "aa": False,
            },
            "Leader": {
                "uuid": None,
                "aa": True,
            },
            "Co-leader": {
                "uuid": None,
                "aa": True,
            },
        }

        position: PositionModel
        for position in positions:
            if (
                position.name not in ("Leader", "Co-leader", "Recruit")
                and position.name not in faction_data["positions"].keys()
            ):
                positions_names.remove(position.name)
                position.delete()
                continue

            positions_data[position.name] = {
                "uuid": position.pid,
                "aa": bool(
                    faction_data["positions"][position.name]["canAccessFactionApi"]
                ),
            }

            position.default = bool(faction_data["positions"][position.name]["default"])
            position.canUseMedicalItem = bool(
                faction_data["positions"][position.name]["canUseMedicalItem"]
            )
            position.canUseBoosterItem = bool(
                faction_data["positions"][position.name]["canUseBoosterItem"]
            )
            position.canUseDrugItem = bool(
                faction_data["positions"][position.name]["canUseDrugItem"]
            )
            position.canUseEnergyRefill = bool(
                faction_data["positions"][position.name]["canUseEnergyRefill"]
            )
            position.canUseNerveRefill = bool(
                faction_data["positions"][position.name]["canUseNerveRefill"]
            )
            position.canLoanTemporaryItem = bool(
                faction_data["positions"][position.name]["canLoanTemporaryItem"]
            )
            position.canLoanWeaponAndArmory = bool(
                faction_data["positions"][position.name]["canLoanWeaponAndArmory"]
            )
            position.canRetrieveLoanedArmory = bool(
                faction_data["positions"][position.name]["canRetrieveLoanedArmory"]
            )
            position.canPlanAndInitiateOrganisedCrime = bool(
                faction_data["positions"][position.name][
                    "canPlanAndInitiateOrganisedCrime"
                ]
            )
            position.canAccessFactionApi = bool(
                faction_data["positions"][position.name]["canAccessFactionApi"]
            )
            position.canGiveItem = bool(
                faction_data["positions"][position.name]["canGiveItem"]
            )
            position.canGiveMoney = bool(
                faction_data["positions"][position.name]["canGiveMoney"]
            )
            position.canGivePoints = bool(
                faction_data["positions"][position.name]["canGivePoints"]
            )
            position.canManageForum = bool(
                faction_data["positions"][position.name]["canManageForum"]
            )
            position.canManageApplications = bool(
                faction_data["positions"][position.name]["canManageApplications"]
            )
            position.canKickMembers = bool(
                faction_data["positions"][position.name]["canKickMembers"]
            )
            position.canAdjustMemberBalance = bool(
                faction_data["positions"][position.name]["canAdjustMemberBalance"]
            )
            position.canManageWars = bool(
                faction_data["positions"][position.name]["canManageWars"]
            )
            position.canManageUpgrades = bool(
                faction_data["positions"][position.name]["canManageUpgrades"]
            )
            position.canSendNewsletter = bool(
                faction_data["positions"][position.name]["canSendNewsletter"]
            )
            position.canChangeAnnouncement = bool(
                faction_data["positions"][position.name]["canChangeAnnouncement"]
            )
            position.canChangeDescription = bool(
                faction_data["positions"][position.name]["canChangeDescription"]
            )
            position.save()

        for position_name, position_data in faction_data["positions"].items():
            if position_name in positions_names:
                continue

            position = PositionModel(
                pid=uuid.uuid4().hex,
                name=position_name,
                factiontid=faction.tid,
            )

            positions_data[position.name] = {
                "uuid": position.pid,
                "aa": bool(
                    faction_data["positions"][position.name]["canAccessFactionApi"]
                ),
            }

            position.default = bool(faction_data["positions"][position.name]["default"])
            position.canUseMedicalItem = bool(
                faction_data["positions"][position.name]["canUseMedicalItem"]
            )
            position.canUseBoosterItem = bool(
                faction_data["positions"][position.name]["canUseBoosterItem"]
            )
            position.canUseDrugItem = bool(
                faction_data["positions"][position.name]["canUseDrugItem"]
            )
            position.canUseEnergyRefill = bool(
                faction_data["positions"][position.name]["canUseEnergyRefill"]
            )
            position.canUseNerveRefill = bool(
                faction_data["positions"][position.name]["canUseNerveRefill"]
            )
            position.canLoanTemporaryItem = bool(
                faction_data["positions"][position.name]["canLoanTemporaryItem"]
            )
            position.canLoanWeaponAndArmory = bool(
                faction_data["positions"][position.name]["canLoanWeaponAndArmory"]
            )
            position.canRetrieveLoanedArmory = bool(
                faction_data["positions"][position.name]["canRetrieveLoanedArmory"]
            )
            position.canPlanAndInitiateOrganisedCrime = bool(
                faction_data["positions"][position.name][
                    "canPlanAndInitiateOrganisedCrime"
                ]
            )
            position.canAccessFactionApi = bool(
                faction_data["positions"][position.name]["canAccessFactionApi"]
            )
            position.canGiveItem = bool(
                faction_data["positions"][position.name]["canGiveItem"]
            )
            position.canGiveMoney = bool(
                faction_data["positions"][position.name]["canGiveMoney"]
            )
            position.canGivePoints = bool(
                faction_data["positions"][position.name]["canGivePoints"]
            )
            position.canManageForum = bool(
                faction_data["positions"][position.name]["canManageForum"]
            )
            position.canManageApplications = bool(
                faction_data["positions"][position.name]["canManageApplications"]
            )
            position.canKickMembers = bool(
                faction_data["positions"][position.name]["canKickMembers"]
            )
            position.canAdjustMemberBalance = bool(
                faction_data["positions"][position.name]["canAdjustMemberBalance"]
            )
            position.canManageWars = bool(
                faction_data["positions"][position.name]["canManageWars"]
            )
            position.canManageUpgrades = bool(
                faction_data["positions"][position.name]["canManageUpgrades"]
            )
            position.canSendNewsletter = bool(
                faction_data["positions"][position.name]["canSendNewsletter"]
            )
            position.canChangeAnnouncement = bool(
                faction_data["positions"][position.name]["canChangeAnnouncement"]
            )
            position.canChangeDescription = bool(
                faction_data["positions"][position.name]["canChangeDescription"]
            )
            position.save()

            positions_names.append(position.name)

        print(positions_data)

        lead_keys = []

        leader = UserModel.objects(tid=faction.leader).first()
        coleader = UserModel.objects(tid=faction.coleader).first()

        if leader is not None and leader.key != "":
            lead_keys.append(leader.key)
        if coleader is not None and coleader.key != "":
            lead_keys.append(coleader.key)

        if len(lead_keys) != 0:
            try:
                user_ts_data = torn_stats_get(
                    f"spy/faction/{faction.tid}", random.choice(lead_keys)
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
                user: UserModel = UserModel.objects(tid=int(member_id)).modify(
                    upsert=True,
                    new=True,
                    set__name=member["name"],
                    set__level=member["level"],
                    set__last_refresh=utils.now(),
                    set__factionid=faction.tid,
                    set__factionaa=positions_data[member["position"]]["aa"],
                    set__faction_position=positions_data[member["position"]]["uuid"],
                    set__status=member["last_action"]["status"],
                    set__last_action=member["last_action"]["timestamp"],
                )
            else:
                user.name = member["name"]
                user.level = member["level"]
                user.last_refresh = utils.now()
                user.factionid = faction.tid
                user.factionaa = positions_data[member["position"]]["aa"]
                user.faction_position = positions_data[member["position"]]["uuid"]
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
            user.faction_position = None
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
                        if (
                            faction.chainod.get(tid) is None
                            and user_od["contributed"] == 1
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
                                    }
                                ],
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
                        elif faction.chainod.get(tid) is not None and user_od[
                            "contributed"
                        ] != faction.chainod.get(tid).get("contributed"):
                            overdosed_user = UserModel.objects(tid=tid).first()
                            payload = {
                                "embeds": [
                                    {
                                        "title": "User Overdose",
                                        "description": f"User {tid if overdosed_user is None else overdosed_user.name} of "
                                        f"faction {faction.name} has overdosed.",
                                        "timestamp": datetime.datetime.utcnow().isoformat(),
                                        "footer": {"text": utils.torn_timestamp()},
                                    }
                                ],
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


@celery_app.task
def fetch_attacks_runner():
    redis = redisdb.get_redis()

    if redis.exists("tornium:celery-lock:fetch-attacks"):  # Lock enabled
        logger.debug("Fetch attacks task terminated due to pre-existing task")
        raise Exception(
            f"Can not run task as task is already being run. Try again in {redis.ttl('tornium:celery-lock:fetch-attack')} seconds."
        )

    if redis.setnx("tornium:celery-lock:fetch-attacks", 1):
        redis.expire("tornium:celery-lock:fetch-attacks", 60)  # Lock for five minutes
    if redis.ttl("torniusm:celery-lock:fetch-attacks") < 0:
        redis.expire("tornium:celery-lock:fetch-attacks", 1)

    requests_session = requests.Session()

    faction: FactionModel
    for faction in FactionModel.objects(
        Q(aa_keys__not__size=0) & Q(aa_keys__exists=True)
    ):
        if len(faction.aa_keys) == 0:
            continue
        elif faction.last_attacks == 0:
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
        except NetworkingError as e:
            logger.exception(e)
            honeybadger.notify(e, context={"code": e.code})
            continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        if "attacks" not in faction_data or len(faction_data["attacks"]) == 0:
            continue

        retal_attacks.delay(
            faction.tid, faction_data, last_attacks=faction.last_attacks
        )
        stat_db_attacks.delay(
            faction.tid, faction_data, last_attacks=faction.last_attacks
        )

        if len(faction_data["attacks"].values()) > 0:
            try:
                faction.last_attacks = list(faction_data["attacks"].values())[-1][
                    "timestamp_ended"
                ]
                faction.save()
            except Exception as e:
                logger.exception(e)


@celery_app.task
def retal_attacks(factiontid, faction_data, last_attacks=None):
    if "attacks" not in faction_data:
        return
    elif len(faction_data["attacks"]) == 0:
        return

    faction: FactionModel = FactionModel.objects(tid=factiontid).first()

    if faction is None:
        return
    elif faction.guild == 0:
        return

    guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

    if guild is None:
        return
    elif faction.tid not in guild.factions:
        return
    elif str(faction.tid) not in guild.retal_config:
        return
    elif guild.retal_config[str(faction.tid)] == 0:
        return

    if last_attacks is None or last_attacks >= utils.now():
        last_attacks = faction.last_attacks

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
        elif attack["timestamp_ended"] <= last_attacks:
            continue
        elif attack["defender_faction"] != faction.tid:  # Not a defend
            continue
        elif attack["attacker_id"] in ("", 0):  # Stealthed attacker
            continue
        elif attack["respect"] == 0:  # Attack by fac member or recruit
            continue

        user: UserModel = UserModel.objects(tid=attack["defender_id"]).first()
        opponent: UserModel = UserModel.objects(tid=attack["attacker_id"]).first()

        if user is None:
            user = UserModel.objects(tid=attack["defender_id"]).modify(
                upsert=True,
                new=True,
                set__name=attack["defender_name"],
                set__factionid=attack["defender_faction"],
            )

        if opponent is None:
            opponent = UserModel.objects(tid=attack["attacker_id"]).modify(
                upsert=True,
                new=True,
                set__name=attack["attacker_name"],
                set__factionid=attack["attacker_faction"],
            )

        if attack["attacker_faction"] == 0:
            title = f"{faction.name} can retal on {opponent.name} [{opponent.tid}]"
        else:
            title = f"{faction.name} can retal on {opponent.name} [{opponent.tid}] from {attack['attacker_factionname']} [{attack['attacker_faction']}]"

        fields = [
            {
                "name": "Timeout",
                "value": f"<t:{attack['timestamp_ended'] + 300}:R>",  # Five minutes after attack ends
            }
        ]

        if attack["modifiers"]["fair_fight"] != 3:
            if (
                user is not None
                and user.battlescore != 0
                and utils.now() - user.battlescore_update <= 259200
            ):  # Three days
                try:
                    opponent_score = user.battlescore / (
                        (attack["modifiers"]["fair_fight"] - 1) * 0.375
                    )
                except DivisionByZero:
                    opponent_score = 0

                if opponent_score != 0:
                    fields.extend(
                        (
                            {
                                "name": "Estimated Stat Score",
                                "value": utils.commas(round(opponent_score)),
                                "inline": True,
                            },
                            {
                                "name": "Stat Score Update",
                                "value": f"<t:{utils.now()}:R>",
                                "inline": True,
                            },
                        )
                    )
        else:
            try:
                if user is not None:
                    stat: StatModel = (
                        StatModel.objects(
                            Q(tid=opponent.tid)
                            & (Q(globalstat=True) | Q(addedfactiontid=user.factionid))
                        )
                        .order_by("-timeadded")
                        .first()
                    )
                else:
                    stat: StatModel = (
                        StatModel.objects(Q(tid=opponent.tid) & Q(globalstat=True))
                        .order_by("-timeadded")
                        .first()
                    )
            except AttributeError as e:
                logger.exception(e),
                stat = None

            if stat is not None:
                fields.extend(
                    (
                        {
                            "name": "Estimated Stat Score",
                            "value": utils.commas(stat.battlescore),
                            "inline": True,
                        },
                        {
                            "name": "Stat Score Update",
                            "value": f"<t:{stat.timeadded}:R>",
                            "inline": True,
                        },
                    )
                )

        if attack["attacker_faction"] in (0, ""):
            pass
        elif attack["chain"] > 100:
            fields.append(
                {
                    "name": "Opponent Faction Chaining",
                    "value": "True",
                    "inline": False,
                }
            )
        else:
            fields.append(
                {"name": "Opponent Faction Chaining", "value": "False", "inline": False}
            )

        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": f"{opponent.name} [{opponent.tid}] {attack['result'].lower()} {user.name} [{user.tid}] (-{attack['respect_loss']})",
                    "fields": fields,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "footer": {"text": utils.torn_timestamp()},
                }
            ],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 5,
                            "label": "Attack Log",
                            "url": f"https://www.torn.com/loader.php?sid=attackLog&ID={attack['code']}",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": "RETAL!!",
                            "url": f"https://www.torn.com/loader.php?sid=attack&user2ID={opponent.tid}",
                        },
                    ],
                },
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 5,
                            "label": f"{opponent.name}",
                            "url": f"https://www.torn.com/profiles.php?XID={opponent.tid}",
                        },
                        {
                            "type": 2,
                            "style": 5,
                            "label": f"{attack['attacker_factionname']}",
                            "url": f"https://www.torn.com/factions.php?step=profile&userID={opponent.tid}",
                        },
                    ],
                },
            ],
        }

        try:
            discordpost.delay(
                f"channels/{guild.retal_config[str(faction.tid)]}/messages",
                payload,
                bucket=f"channels/{guild.retal_config[str(faction.tid)]}",
                dev=guild.skynet,
            )
        except utils.DiscordError as e:
            if e.code == 10003:
                logger.warning(
                    f"Unknown retal channel {guild.retal_config[str(faction.tid)]} in guild {guild.sid}"
                )
                return

            logger.exception(e)
            honeybadger.notify(e)
            continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue


@celery_app.task
def stat_db_attacks(factiontid, faction_data, last_attacks=None):
    if len(faction_data) == 0:
        return
    elif "attacks" not in faction_data:
        return
    elif len(faction_data["attacks"]) == 0:
        return

    faction: FactionModel = FactionModel.objects(tid=factiontid).first()

    if faction is None:
        return
    elif faction.config.get("stats") in (0, None):
        return

    if last_attacks is None or last_attacks >= utils.now():
        last_attacks = faction.last_attacks

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
        elif attack["modifiers"]["fair_fight"] in (
            1,
            3,
        ):  # 3x FF can be greater than the defender battlescore indicated
            continue
        elif attack["timestamp_ended"] <= last_attacks:
            continue

        # User: faction member
        # Opponent: non-faction member regardless of attack or defend

        if (
            attack["defender_faction"] == faction_data["ID"]
        ):  # Defender fac is the fac making the call

            if attack["attacker_id"] in ("", 0):  # Attacker stealthed
                continue
            elif attack["respect"] == 0:  # Attack by fac member
                continue

            user: UserModel = UserModel.objects(tid=attack["defender_id"]).first()
            user_id = attack["defender_id"]

            if user is None:
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
                honeybadger.notify(e)
                continue

            # TODO: Update
            if user_score > 100000 or user_score == 0:  # 100k old value
                continue

            opponent: UserModel = UserModel.objects(tid=attack["attacker_id"]).first()
            opponent_id = attack["attacker_id"]

            if opponent is None:
                opponent = UserModel.objects(tid=attack["attacker_id"]).modify(
                    upsert=True,
                    new=True,
                    set__name=attack["attacker_name"],
                    set__factionid=attack["attacker_faction"],
                )
        else:  # User is the attacker
            user: UserModel = UserModel.objects(tid=attack["attacker_id"]).first()
            user_id = attack["attacker_id"]

            if user is None:
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
                honeybadger.notify(e)
                continue

            if user_score == 0:
                continue

            opponent: UserModel = UserModel.objects(tid=attack["defender_id"]).first()
            opponent_id = attack["defender_id"]

            if opponent is None:
                opponent = UserModel.objects(tid=attack["attacker_id"]).modify(
                    upsert=True,
                    new=True,
                    set__name=attack["attacker_name"],
                    set__factionid=attack["attacker_faction"],
                )

        if opponent is None:
            try:
                update_user.delay(tid=opponent_id, key=random.choice(faction.aa_keys))
            except TornError as e:
                logger.exception(e)
                honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
                continue
            except Exception as e:
                logger.exception(e)
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

        stat_faction: FactionModel = FactionModel.objects(tid=user.factionid).first()

        if stat_faction is None or user.factionid == 0:
            globalstat = 1
        else:
            globalstat = stat_faction.statconfig["global"]

        try:
            stat_entry = StatModel(
                statid=StatModel.objects().order_by("-statid").first().statid + 1,
                tid=opponent_id,
                battlescore=opponent_score,
                timeadded=attack["timestamp_ended"],
                addedid=user_id,
                addedfactiontid=user.factionid,
                globalstat=globalstat,
            )
            stat_entry.save()
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue
