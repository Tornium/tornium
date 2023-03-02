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
import logging
import math
import random
import typing
import uuid
from decimal import DivisionByZero

import mongoengine
import requests
from mongoengine.queryset.visitor import Q
from pymongo.errors import BulkWriteError

import redisdb
import skynet.skyutils
import utils
from models.attackmodel import AttackModel
from models.factionmodel import FactionModel
from models.ocmodel import OCModel
from models.positionmodel import PositionModel
from models.servermodel import ServerModel
from models.statmodel import StatModel
from models.usermodel import UserModel
from models.withdrawalmodel import WithdrawalModel
from tasks import celery_app, logger
from tasks.api import tornget, discordpatch, discordpost, torn_stats_get
from tasks.user import update_user
from utils.errors import NetworkingError, TornError

logger: logging.Logger

ORGANIZED_CRIMES = {
    1: "Blackmail",
    2: "Kidnapping",
    3: "Bomb Threat",
    4: "Planned Robbery",
    5: "Rob a Money Train",
    6: "Take over a Cruise Liner",
    7: "Hijack a Plane",
    8: "Political Assassination",
}

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
        except (TornError, NetworkingError):
            continue
        except Exception as e:
            logger.exception(e)
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
                "aa": bool(faction_data["positions"][position.name]["canAccessFactionApi"]),
            }

            position.default = bool(faction_data["positions"][position.name]["default"])
            position.canUseMedicalItem = bool(faction_data["positions"][position.name]["canUseMedicalItem"])
            position.canUseBoosterItem = bool(faction_data["positions"][position.name]["canUseBoosterItem"])
            position.canUseDrugItem = bool(faction_data["positions"][position.name]["canUseDrugItem"])
            position.canUseEnergyRefill = bool(faction_data["positions"][position.name]["canUseEnergyRefill"])
            position.canUseNerveRefill = bool(faction_data["positions"][position.name]["canUseNerveRefill"])
            position.canLoanTemporaryItem = bool(faction_data["positions"][position.name]["canLoanTemporaryItem"])
            position.canLoanWeaponAndArmory = bool(faction_data["positions"][position.name]["canLoanWeaponAndArmory"])
            position.canRetrieveLoanedArmory = bool(faction_data["positions"][position.name]["canRetrieveLoanedArmory"])
            position.canPlanAndInitiateOrganisedCrime = bool(
                faction_data["positions"][position.name]["canPlanAndInitiateOrganisedCrime"]
            )
            position.canAccessFactionApi = bool(faction_data["positions"][position.name]["canAccessFactionApi"])
            position.canGiveItem = bool(faction_data["positions"][position.name]["canGiveItem"])
            position.canGiveMoney = bool(faction_data["positions"][position.name]["canGiveMoney"])
            position.canGivePoints = bool(faction_data["positions"][position.name]["canGivePoints"])
            position.canManageForum = bool(faction_data["positions"][position.name]["canManageForum"])
            position.canManageApplications = bool(faction_data["positions"][position.name]["canManageApplications"])
            position.canKickMembers = bool(faction_data["positions"][position.name]["canKickMembers"])
            position.canAdjustMemberBalance = bool(faction_data["positions"][position.name]["canAdjustMemberBalance"])
            position.canManageWars = bool(faction_data["positions"][position.name]["canManageWars"])
            position.canManageUpgrades = bool(faction_data["positions"][position.name]["canManageUpgrades"])
            position.canSendNewsletter = bool(faction_data["positions"][position.name]["canSendNewsletter"])
            position.canChangeAnnouncement = bool(faction_data["positions"][position.name]["canChangeAnnouncement"])
            position.canChangeDescription = bool(faction_data["positions"][position.name]["canChangeDescription"])
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
                "aa": bool(faction_data["positions"][position.name]["canAccessFactionApi"]),
            }

            position.default = bool(faction_data["positions"][position.name]["default"])
            position.canUseMedicalItem = bool(faction_data["positions"][position.name]["canUseMedicalItem"])
            position.canUseBoosterItem = bool(faction_data["positions"][position.name]["canUseBoosterItem"])
            position.canUseDrugItem = bool(faction_data["positions"][position.name]["canUseDrugItem"])
            position.canUseEnergyRefill = bool(faction_data["positions"][position.name]["canUseEnergyRefill"])
            position.canUseNerveRefill = bool(faction_data["positions"][position.name]["canUseNerveRefill"])
            position.canLoanTemporaryItem = bool(faction_data["positions"][position.name]["canLoanTemporaryItem"])
            position.canLoanWeaponAndArmory = bool(faction_data["positions"][position.name]["canLoanWeaponAndArmory"])
            position.canRetrieveLoanedArmory = bool(faction_data["positions"][position.name]["canRetrieveLoanedArmory"])
            position.canPlanAndInitiateOrganisedCrime = bool(
                faction_data["positions"][position.name]["canPlanAndInitiateOrganisedCrime"]
            )
            position.canAccessFactionApi = bool(faction_data["positions"][position.name]["canAccessFactionApi"])
            position.canGiveItem = bool(faction_data["positions"][position.name]["canGiveItem"])
            position.canGiveMoney = bool(faction_data["positions"][position.name]["canGiveMoney"])
            position.canGivePoints = bool(faction_data["positions"][position.name]["canGivePoints"])
            position.canManageForum = bool(faction_data["positions"][position.name]["canManageForum"])
            position.canManageApplications = bool(faction_data["positions"][position.name]["canManageApplications"])
            position.canKickMembers = bool(faction_data["positions"][position.name]["canKickMembers"])
            position.canAdjustMemberBalance = bool(faction_data["positions"][position.name]["canAdjustMemberBalance"])
            position.canManageWars = bool(faction_data["positions"][position.name]["canManageWars"])
            position.canManageUpgrades = bool(faction_data["positions"][position.name]["canManageUpgrades"])
            position.canSendNewsletter = bool(faction_data["positions"][position.name]["canSendNewsletter"])
            position.canChangeAnnouncement = bool(faction_data["positions"][position.name]["canChangeAnnouncement"])
            position.canChangeDescription = bool(faction_data["positions"][position.name]["canChangeDescription"])
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
                user_ts_data = torn_stats_get(f"spy/faction/{faction.tid}", random.choice(lead_keys))
            except NetworkingError:
                continue
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
            except (TornError, NetworkingError):
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
                        if faction.chainod.get(tid) is None and user_od["contributed"] == 1:
                            overdosed_user = UserModel.objects(tid=tid).first()
                            payload = {
                                "embeds": [
                                    {
                                        "title": "User Overdose",
                                        "description": f"User {tid if overdosed_user is None else overdosed_user.name} "
                                        f"of faction {faction.name} has overdosed.",
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
                                )
                            except Exception as e:
                                logger.exception(e)
                                continue
                        elif faction.chainod.get(tid) is not None and user_od["contributed"] != faction.chainod.get(
                            tid
                        ).get("contributed"):
                            overdosed_user = UserModel.objects(tid=tid).first()
                            payload = {
                                "embeds": [
                                    {
                                        "title": "User Overdose",
                                        "description": f"User {tid if overdosed_user is None else overdosed_user.name} "
                                        f"of faction {faction.name} has overdosed.",
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
                                )
                            except Exception as e:
                                logger.exception(e)
                                continue
                    except Exception as e:
                        logger.exception(e)
                        continue

            faction.chainod = faction_od["contributors"]["drugoverdoses"]

        faction.save()


@celery_app.task
def fetch_attacks_runner():
    redis = redisdb.get_redis()

    if (
        redis.exists("tornium:celery-lock:fetch-attacks") and redis.ttl("tornium:celery-lock:fetch-attacks") > 1
    ):  # Lock enabled
        logger.debug("Fetch attacks task terminated due to pre-existing task")
        raise Exception(
            f"Can not run task as task is already being run. Try again in "
            f"{redis.ttl('tornium:celery-lock:fetch-attacks')} seconds."
        )

    if redis.setnx("tornium:celery-lock:fetch-attacks", 1):
        redis.expire("tornium:celery-lock:fetch-attacks", 60)  # Lock for five minutes
    if redis.ttl("tornium:celery-lock:fetch-attacks") < 1:
        redis.expire("tornium:celery-lock:fetch-attacks", 1)

    requests_session = requests.Session()

    faction: FactionModel
    for faction in FactionModel.objects(Q(aa_keys__exists=True) & Q(aa_keys__not__size=0)):
        if len(faction.aa_keys) == 0:
            continue
        elif faction.last_attacks == 0:
            faction.last_attacks = utils.now()
            faction.save()
            continue

        aa_key = random.choice(faction.aa_keys)

        try:
            faction_data = tornget(
                "faction/?selections=basic,attacks",
                fromts=faction.last_attacks + 1,  # Timestamp is inclusive
                key=aa_key,
                session=requests_session,
            )
        except TornError as e:
            if e.code == 7:
                db_aa_keys = list(faction.aa_keys)

                try:
                    db_aa_keys.remove(aa_key)
                    faction.aa_keys = db_aa_keys
                    faction.save()
                except ValueError:
                    pass
            continue
        except NetworkingError:
            continue
        except Exception as e:
            logger.exception(e)
            continue

        if "attacks" not in faction_data or len(faction_data["attacks"]) == 0:
            continue

        retal_attacks.delay(faction.tid, faction_data, last_attacks=faction.last_attacks)
        stat_db_attacks.delay(faction.tid, faction_data, last_attacks=faction.last_attacks)

        if len(faction_data["attacks"].values()) > 0:
            try:
                faction.last_attacks = list(faction_data["attacks"].values())[-1]["timestamp_ended"]
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
            title = (
                f"{faction.name} can retal on {opponent.name} [{opponent.tid}] from "
                f"{attack['attacker_factionname']} [{attack['attacker_faction']}]"
            )

        fields = [
            {
                "name": "Timeout",
                "value": f"<t:{attack['timestamp_ended'] + 300}:R>",  # Five minutes after attack ends
            }
        ]

        if attack["modifiers"]["fair_fight"] != 3:
            if (
                user is not None and user.battlescore != 0 and utils.now() - user.battlescore_update <= 259200
            ):  # Three days
                try:
                    opponent_score = user.battlescore / ((attack["modifiers"]["fair_fight"] - 1) * 0.375)
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
                            Q(tid=opponent.tid) & (Q(globalstat=True) | Q(addedfactiontid=user.factionid))
                        )
                        .order_by("-timeadded")
                        .first()
                    )
                else:
                    stat: StatModel = (
                        StatModel.objects(Q(tid=opponent.tid) & Q(globalstat=True)).order_by("-timeadded").first()
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
            fields.append({"name": "Opponent Faction Chaining", "value": "False", "inline": False})

        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": f"{opponent.name} [{opponent.tid}] {attack['result'].lower()} {user.name} "
                    f"[{user.tid}] (-{attack['respect_loss']})",
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
            )
        except utils.DiscordError as e:
            if e.code == 10003:
                logger.warning(f"Unknown retal channel {guild.retal_config[str(faction.tid)]} in guild {guild.sid}")
                return

            logger.exception(e)
            continue
        except Exception as e:
            logger.exception(e)
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

    attacks_data = []

    attack: dict
    for attack in faction_data["attacks"].values():
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
        elif attack["timestamp_ended"] <= last_attacks:
            continue

        # User: faction member
        # Opponent: non-faction member regardless of attack or defend

        if attack["defender_faction"] == faction_data["ID"]:  # Defender fac is the fac making the call
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
                continue

            if user_score == 0:
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
                continue

            if user_score == 0:
                continue

            opponent: UserModel = UserModel.objects(tid=attack["defender_id"]).first()
            opponent_id = attack["defender_id"]

            if opponent is None:
                opponent = UserModel.objects(tid=attack["defender_id"]).modify(
                    upsert=True,
                    new=True,
                    set__name=attack["defender_name"],
                    set__factionid=attack["defender_faction"],
                )

        try:
            update_user.delay(tid=opponent_id, key=random.choice(faction.aa_keys))
        except (TornError, NetworkingError):
            continue
        except Exception as e:
            logger.exception(e)
            continue

        try:
            if attack["defender_faction"] == faction_data["ID"]:
                opponent_score = user_score / ((attack["modifiers"]["fair_fight"] - 1) * 0.375)
            else:
                opponent_score = (attack["modifiers"]["fair_fight"] - 1) * 0.375 * user_score
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
                tid=opponent_id,
                battlescore=opponent_score,
                timeadded=attack["timestamp_ended"],
                addedid=user_id,
                addedfactiontid=user.factionid,
                globalstat=globalstat,
            )
            stat_entry.save()
        except mongoengine.errors.NotUniqueError:
            continue
        except Exception as e:
            logger.exception(e)
            continue

    # Resolves duplicate keys: https://github.com/MongoEngine/mongoengine/issues/1465#issuecomment-445443894
    try:
        attacks_data = [AttackModel(**attack).to_mongo() for attack in attacks_data]
        AttackModel._get_collection().insert_many(attacks_data, ordered=False)
    except BulkWriteError:
        logger.warning(
            f"Attack data (from TID {factiontid}) bulk insert failed. Duplicates may have been found and "
            f"were skipped."
        )


@celery_app.task
def oc_refresh():
    requests_session = requests.Session()

    faction: FactionModel
    for faction in FactionModel.objects(Q(aa_keys__exists=True) & Q(aa_keys__not__size=0)):
        if len(faction.aa_keys) == 0:
            continue
        elif faction.guild in (None, 0):
            continue

        guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

        if guild is None:
            continue
        elif faction.tid not in guild.factions:
            continue
        elif str(faction.tid) not in guild.oc_config:
            continue

        aa_key = random.choice(faction.aa_keys)

        try:
            oc_data = tornget(
                "faction/?selections=crimes",
                key=aa_key,
                session=requests_session,
            )
        except TornError as e:
            if e.code == 7:
                db_aa_keys = list(faction.aa_keys)

                try:
                    db_aa_keys.remove(aa_key)
                    faction.aa_keys = db_aa_keys
                    faction.save()
                except ValueError:
                    pass
            continue
        except NetworkingError:
            continue
        except Exception as e:
            logger.exception(e)
            continue

        OC_DELAY = guild.oc_config[str(faction.tid)]["delay"]["channel"] != 0
        OC_READY = guild.oc_config[str(faction.tid)]["ready"]["channel"] != 0

        for oc_id, oc_data in oc_data["crimes"].items():
            oc_db_original: mongoengine.QuerySet = OCModel.objects(Q(factiontid=faction.tid) & Q(ocid=oc_id))

            oc_db: OCModel = oc_db_original.modify(
                upsert=True,
                new=True,
                set__crime_id=oc_data["crime_id"],
                set__participants=[int(list(participant.keys())[0]) for participant in oc_data["participants"]],
                set__time_started=oc_data["time_started"],
                set__time_ready=oc_data["time_ready"],
                set__time_completed=oc_data["time_completed"],
                set__planned_by=oc_data["planned_by"],
                set__initiated_by=oc_data["initiated_by"],
                set__money_gain=oc_data["money_gain"],
                set__respect_gain=oc_data["respect_gain"],
            )

            oc_db_original = oc_db_original.first()

            if oc_db_original is None:
                continue
            elif oc_db.time_completed != 0:
                continue
            elif oc_db.time_ready > utils.now():
                continue

            ready = list(
                map(
                    lambda participant: list(participant.values())[0]["color"] == "green",
                    oc_data["participants"],
                )
            )

            if OC_DELAY and len(oc_db.delayers) == 0 and not all(ready):
                # OC has been delayed
                oc_db.notified = False

                payload = {
                    "embeds": [
                        {
                            "title": f"OC of {faction.name} Delayed",
                            "description": f"{ORGANIZED_CRIMES[oc_data['crime_id']]} has been delayed "
                            f"({ready.count(True)}/{len(oc_data['participants'])}).",
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": f"#{oc_db.ocid}"},
                        }
                    ],
                    "components": [],
                }

                roles = guild.oc_config[str(faction.tid)]["delay"]["roles"]

                if len(roles) != 0:
                    roles_str = ""

                    for role in roles:
                        roles_str += f"<@&{role}>"

                    payload["content"] = roles_str

                for participant in oc_data["participants"]:
                    participant_id = list(participant.keys())[0]
                    participant = participant[participant_id]

                    if participant["color"] != "green":
                        oc_db.delayers.append(participant_id)

                        participant_db: UserModel = UserModel.objects(tid=participant_id).first()

                        if participant_db is None:
                            payload["components"].append(
                                {
                                    "type": 1,
                                    "components": [
                                        {
                                            "type": 2,
                                            "style": 5,
                                            "label": f"Unknown [{participant_id}]",
                                            "url": f"https://www.torn.com/profiles.php?XID={participant_id}",
                                        },
                                        {
                                            "type": 2,
                                            "style": 2,
                                            "label": f"{participant['description']}",
                                            "custom_id": f"participant:delay:{participant_id}",
                                            "disabled": True,
                                        },
                                    ],
                                }
                            )
                        else:
                            payload["components"].append(
                                {
                                    "type": 1,
                                    "components": [
                                        {
                                            "type": 2,
                                            "style": 5,
                                            "label": f"{participant_db.name} [{participant_id}]",
                                            "url": f"https://www.torn.com/profiles.php?XID={participant_id}",
                                        },
                                        {
                                            "type": 2,
                                            "style": 2,
                                            "label": f"{participant['description']}",
                                            "custom_id": f"participant:delay:{participant_id}",
                                            "disabled": True,
                                        },
                                    ],
                                }
                            )

                oc_db.save()

                try:
                    discordpost.delay(
                        f'channels/{guild.oc_config[str(faction.tid)]["delay"]["channel"]}/messages',
                        payload=payload,
                    )
                except Exception as e:
                    logger.exception(e)
                    continue
            elif OC_READY and not oc_db.notified and all(ready):
                # OC is ready
                oc_db.notified = True
                oc_db.save()

                payload = {
                    "embeds": [
                        {
                            "title": f"OC of {faction.name} Ready",
                            "description": f"{ORGANIZED_CRIMES[oc_data['crime_id']]} is ready.",
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": f"#{oc_db.ocid}"},
                        }
                    ],
                }

                roles = guild.oc_config[str(faction.tid)]["ready"]["roles"]

                if len(roles) != 0:
                    roles_str = ""

                    for role in roles:
                        roles_str += f"<@&{role}>"

                    payload["content"] = roles_str

                try:
                    discordpost.delay(
                        f'channels/{guild.oc_config[str(faction.tid)]["delay"]["channel"]}/messages',
                        payload=payload,
                    )
                except Exception as e:
                    logger.exception(e)
                    continue


@celery_app.task
def auto_cancel_requests():
    withdrawal: WithdrawalModel
    for withdrawal in WithdrawalModel.objects(time_requested__gte=utils.now() - 7200):  # Two hours before now
        if utils.now() - withdrawal.time_requested < 3600:
            continue
        elif withdrawal.fulfiller != 0:
            continue

        withdrawal.fulfiller = -1
        withdrawal.time_fulfilled = utils.now()
        withdrawal.save()

        requester: typing.Optional[UserModel] = UserModel.objects(tid=withdrawal.requester).first()

        if requester is None or requester.discord_id in (0, None, ""):
            continue

        faction: typing.Optional[FactionModel] = FactionModel.objects(tid=withdrawal.factiontid).first()

        try:
            if faction is not None:
                discordpatch(
                    f"channels/{faction.vaultconfig['banking']}/messages/{withdrawal.withdrawal_message}",
                    {
                        "embeds": [
                            {
                                "title": f"Vault Request #{withdrawal.wid}",
                                "description": "This request has timed-out and been automatically cancelled by the "
                                "system.",
                                "fields": [
                                    {
                                        "name": "Original Request Amount",
                                        "value": utils.commas(withdrawal.amount),
                                    },
                                    {
                                        "name": "Original Request Type",
                                        "value": "Points" if withdrawal.wtype == 1 else "Cash",
                                    },
                                    {
                                        "name": "Original Requester",
                                        "value": f"{requester.name} [{requester.tid}]",
                                    },
                                ],
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "color": skynet.skyutils.SKYNET_ERROR,
                            }
                        ],
                        "components": [
                            {
                                "type": 1,
                                "components": [
                                    {
                                        "type": 2,
                                        "style": 5,
                                        "label": "Faction Vault",
                                        "url": "https://www.torn.com/factions.php?step=your#/tab=controls&option=give-to-user",
                                    },
                                    {
                                        "type": 2,
                                        "style": 5,
                                        "label": "Fulfill",
                                        "url": f"https://tornium.com/faction/banking/fulfill/{withdrawal.wid}",
                                    },
                                    {
                                        "type": 2,
                                        "style": 3,
                                        "label": "Fulfill Manually",
                                        "custom_id": "faction:vault:fulfill",
                                    },
                                    {
                                        "type": 2,
                                        "style": 4,
                                        "label": "Cancel",
                                        "custom_id": "faction:vault:cancel",
                                    },
                                ],
                            }
                        ],
                    },
                )
        except (utils.DiscordError, utils.NetworkingError):
            pass
        except Exception as e:
            logger.exception(e)

        try:
            dm_channel = discordpost("users/@me/channels", payload={"recipient_id": requester.discord_id})
        except (utils.DiscordError, utils.NetworkingError):
            continue
        except Exception as e:
            logger.exception(e)
            continue

        discordpost.delay(
            f"channels/{dm_channel['id']}/messages",
            payload={
                "embeds": [
                    {
                        "title": "Vault Request Cancelled",
                        "description": f"Your vault request #{withdrawal.wid} has timed-out and has been automatically "
                        f"cancelled. Vault requests will be automatically cancelled after about an hour. If "
                        f"you still require this, please submit a new request.",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "color": skynet.skyutils.SKYNET_ERROR,
                    }
                ]
            },
        )
