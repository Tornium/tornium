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
import random
import time
import typing
import uuid
from decimal import DivisionByZero

import celery
import mongoengine
from celery.utils.log import get_task_logger
from mongoengine.queryset.visitor import Q
from tornium_commons import rds
from tornium_commons.errors import DiscordError, NetworkingError, TornError
from tornium_commons.formatters import commas, torn_timestamp
from tornium_commons.models import (
    FactionModel,
    OCModel,
    PositionModel,
    ServerModel,
    StatModel,
    UserModel,
    WithdrawalModel,
)
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO

from .api import discordpatch, discordpost, torn_stats_get, tornget
from .user import update_user

logger = get_task_logger(__name__)

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


@celery.shared_task(name="tasks.faction.refresh_factions", routing_key="default.refresh_factions", queue="default")
def refresh_factions():
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

        tornget.signature(
            kwargs={
                "endpoint": "faction/?selections=basic,positions",
                "key": random.choice(keys),
            },
            queue="api",
        ).apply_async(expires=300, link=update_faction.s())

        ts_key = ""
        leader = UserModel.objects(tid=faction.leader).first()

        if leader is not None and leader.key != "":
            ts_key = leader.key
        else:
            coleader = UserModel.objects(tid=faction.coleader).first()

            if coleader is not None and coleader.key != "":
                ts_key = coleader.key

        if ts_key != "":
            torn_stats_get.signature(
                kwargs={"endpoint": f"spy/faction/{faction.tid}", "key": ts_key},
                queue="api",
            ).apply_async(
                expires=300,
                link=update_faction_ts.s(),
            )

        if faction.od_channel != 0 and faction.guild not in (0, None):
            try:
                tornget.signature(
                    kwargs={
                        "endpoint": "faction/?selections=basic,contributors",
                        "stat": "drugoverdoses",
                        "key": random.choice(keys),
                    },
                    queue="api",
                ).apply_async(
                    expires=300,
                    link=check_faction_ods.s(),
                )
            except (TornError, NetworkingError):
                continue
            except Exception as e:
                logger.exception(e)
                continue


@celery.shared_task(name="tasks.faction.update_faction", routing_key="quick.update_faction", queue="quick")
def update_faction(faction_data):
    if faction_data is None:
        return

    faction = FactionModel.objects(tid=faction_data["ID"]).modify(
        upsert=True,
        new=True,
        set__name=faction_data["name"],
        set__respect=faction_data["respect"],
        set__capacity=faction_data["capacity"],
        set__leader=faction_data["leader"],
        set__coleader=faction_data["co-leader"],
        set__last_members=int(time.time()),
    )

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

        position_perms = faction_data["positions"][position.name]
        positions_data[position.name] = {
            "uuid": position.pid,
            "aa": bool(faction_data["positions"][position.name]["canAccessFactionApi"]),
        }

        position.default = bool(position_perms["default"])
        position.canUseMedicalItem = bool(position_perms["canUseMedicalItem"])
        position.canUseBoosterItem = bool(position_perms["canUseBoosterItem"])
        position.canUseDrugItem = bool(position_perms["canUseDrugItem"])
        position.canUseEnergyRefill = bool(position_perms["canUseEnergyRefill"])
        position.canUseNerveRefill = bool(position_perms["canUseNerveRefill"])
        position.canLoanTemporaryItem = bool(position_perms["canLoanTemporaryItem"])
        position.canLoanWeaponAndArmory = bool(position_perms["canLoanWeaponAndArmory"])
        position.canRetrieveLoanedArmory = bool(position_perms["canRetrieveLoanedArmory"])
        position.canPlanAndInitiateOrganisedCrime = bool(position_perms["canPlanAndInitiateOrganisedCrime"])
        position.canAccessFactionApi = bool(position_perms["canAccessFactionApi"])
        position.canGiveItem = bool(position_perms["canGiveItem"])
        position.canGiveMoney = bool(position_perms["canGiveMoney"])
        position.canGivePoints = bool(position_perms["canGivePoints"])
        position.canManageForum = bool(position_perms["canManageForum"])
        position.canManageApplications = bool(position_perms["canManageApplications"])
        position.canKickMembers = bool(position_perms["canKickMembers"])
        position.canAdjustMemberBalance = bool(position_perms["canAdjustMemberBalance"])
        position.canManageWars = bool(position_perms["canManageWars"])
        position.canManageUpgrades = bool(position_perms["canManageUpgrades"])
        position.canSendNewsletter = bool(position_perms["canSendNewsletter"])
        position.canChangeAnnouncement = bool(position_perms["canChangeAnnouncement"])
        position.canChangeDescription = bool(position_perms["canChangeDescription"])
        position.save()

    for position_name, position_data in faction_data["positions"].items():
        if position_name in positions_names:
            continue

        position = PositionModel(
            pid=uuid.uuid4().hex,
            name=position_name,
            factiontid=faction.tid,
        )

        position_perms = faction_data["positions"][position.name]
        positions_data[position.name] = {
            "uuid": position.pid,
            "aa": bool(faction_data["positions"][position.name]["canAccessFactionApi"]),
        }

        position.default = bool(position_perms["default"])
        position.canUseMedicalItem = bool(position_perms["canUseMedicalItem"])
        position.canUseBoosterItem = bool(position_perms["canUseBoosterItem"])
        position.canUseDrugItem = bool(position_perms["canUseDrugItem"])
        position.canUseEnergyRefill = bool(position_perms["canUseEnergyRefill"])
        position.canUseNerveRefill = bool(position_perms["canUseNerveRefill"])
        position.canLoanTemporaryItem = bool(position_perms["canLoanTemporaryItem"])
        position.canLoanWeaponAndArmory = bool(position_perms["canLoanWeaponAndArmory"])
        position.canRetrieveLoanedArmory = bool(position_perms["canRetrieveLoanedArmory"])
        position.canPlanAndInitiateOrganisedCrime = bool(position_perms["canPlanAndInitiateOrganisedCrime"])
        position.canAccessFactionApi = bool(position_perms["canAccessFactionApi"])
        position.canGiveItem = bool(position_perms["canGiveItem"])
        position.canGiveMoney = bool(position_perms["canGiveMoney"])
        position.canGivePoints = bool(position_perms["canGivePoints"])
        position.canManageForum = bool(position_perms["canManageForum"])
        position.canManageApplications = bool(position_perms["canManageApplications"])
        position.canKickMembers = bool(position_perms["canKickMembers"])
        position.canAdjustMemberBalance = bool(position_perms["canAdjustMemberBalance"])
        position.canManageWars = bool(position_perms["canManageWars"])
        position.canManageUpgrades = bool(position_perms["canManageUpgrades"])
        position.canSendNewsletter = bool(position_perms["canSendNewsletter"])
        position.canChangeAnnouncement = bool(position_perms["canChangeAnnouncement"])
        position.canChangeDescription = bool(position_perms["canChangeDescription"])
        position.save()

    users = []

    for member_id, member in faction_data["members"].items():
        users.append(int(member_id))

        UserModel.objects(tid=int(member_id)).modify(
            upsert=True,
            new=True,
            set__name=member["name"],
            set__level=member["level"],
            set__last_refresh=int(time.time()),
            set__factionid=faction.tid,
            set__factionaa=positions_data[member["position"]]["aa"] if member["position"] is not None else False,
            set__faction_position=positions_data[member["position"]]["uuid"],
            set__status=member["last_action"]["status"],
            set__last_action=member["last_action"]["timestamp"],
        )

    for user in UserModel.objects(factionid=faction.tid):
        if user.tid in users:
            continue

        user.factionid = 0
        user.faction_position = None
        user.factionaa = False
        user.save()


@celery.shared_task(name="tasks.faction.update_faction_ts", routing_key="default.update_faction_ts", queue="default")
def update_faction_ts(faction_ts_data):
    if not faction_ts_data["status"]:
        return

    for user_id, user_data in faction_ts_data["faction"]["members"].items():
        if "spy" not in user_data:
            continue

        user: UserModel = UserModel.objects(tid=int(user_id)).first()

        if user is None:
            continue
        elif user.key not in ("", None):
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


@celery.shared_task(name="tasks.faction.check_faction_ods", routing_key="quick.check_faction_ods", queue="quick")
def check_faction_ods(faction_od_data):
    factionid = faction_od_data["ID"]
    faction: FactionModel = FactionModel.objects(tid=factionid).first()

    if faction is None:
        return
    elif len(faction.chainod) == 0:
        faction.chainod = faction_od_data["contributors"]["drugoverdoses"]
        faction.save()
        return
    elif faction.od_channel in (0, None):
        return

    # channel_data = discordget(f"channels/{faction.od_channel}", channel=faction.od_channel)
    #
    # if channel_data.get("guild_id") != faction.guild:
    #     faction.od_channel = 0
    #     faction.save()
    #     return

    guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

    if guild is None:
        faction.chainod = faction_od_data["contributors"]["drugoverdoses"]
        faction.save()
        return

    for tid, user_od in faction_od_data["contributors"]["drugoverdoses"].items():
        if faction.chainod.get(tid) is None and user_od["contributed"] > 0:
            overdosed_user = UserModel.objects(tid=tid).first()
            payload = {
                "embeds": [
                    {
                        "title": "User Overdose",
                        "description": f"User {tid if overdosed_user is None else overdosed_user.name} "
                        f"of faction {faction.name} has overdosed.",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": torn_timestamp()},
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

            discordpost.delay(
                f"channels/{faction.od_channel}/messages",
                payload=payload,
                channel=faction.od_channel,
            ).forget()
        elif faction.chainod.get(tid) is not None and user_od["contributed"] != faction.chainod.get(tid).get(
            "contributed"
        ):
            overdosed_user = UserModel.objects(tid=tid).first()
            payload = {
                "embeds": [
                    {
                        "title": "User Overdose",
                        "description": f"User {tid if overdosed_user is None else overdosed_user.name} "
                        f"of faction {faction.name} has overdosed.",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": torn_timestamp()},
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

            discordpost.delay(
                f"channels/{faction.od_channel}/messages",
                payload=payload,
                channel=faction.od_channel,
            ).forget()

    faction.chainod = faction_od_data["contributors"]["drugoverdoses"]
    faction.save()


@celery.shared_task(name="tasks.faction.fetch_attacks_runner", routing_key="quick.fetch_attacks_runner", queue="quick")
def fetch_attacks_runner():
    redis = rds()

    if (
        redis.exists("tornium:celery-lock:fetch-attacks") and redis.ttl("tornium:celery-lock:fetch-attacks") > 1
    ):  # Lock enabled
        logger.debug("Fetch attacks task terminated due to pre-existing task")
        raise Exception(
            f"Can not run task as task is already being run. Try again in "
            f"{redis.ttl('tornium:celery-lock:fetch-attacks')} seconds."
        )

    if redis.setnx("tornium:celery-lock:fetch-attacks", 1):
        redis.expire("tornium:celery-lock:fetch-attacks", 60)  # Lock for one minute
    if redis.ttl("tornium:celery-lock:fetch-attacks") < 1:
        redis.expire("tornium:celery-lock:fetch-attacks", 1)

    faction: FactionModel
    for faction in FactionModel.objects(Q(aa_keys__exists=True) & Q(aa_keys__not__size=0)):
        if len(faction.aa_keys) == 0:
            continue
        elif faction.last_attacks == 0:
            faction.last_attacks = int(time.time())
            faction.save()
            continue
        elif time.time() - faction.last_attacks > 86400:  # One day
            # Prevents old data from being added (especially for retals)
            faction.last_attacks = int(time.time())
            faction.save()
            continue

        aa_key = random.choice(faction.aa_keys)

        tornget.signature(
            kwargs={
                "endpoint": "faction/?selections=basic,attacks",
                "fromts": faction.last_attacks + 1,  # timestamp is inclusive
                "key": aa_key,
            },
            queue="api",
        ).apply_async(
            expires=300,
            link=celery.group(
                retal_attacks.signature(
                    kwargs={
                        "last_attacks": faction.last_attacks,
                    },
                    queue="quick",
                ),
                stat_db_attacks.signature(
                    kwargs={
                        "last_attacks": faction.last_attacks,
                    },
                    queue="quick",
                ),
            ),
        )


@celery.shared_task(name="tasks.faction.retal_attacks", routing_key="quick.retal_attacks", queue="quick")
def retal_attacks(faction_data, last_attacks=None):
    if "attacks" not in faction_data:
        return
    elif len(faction_data["attacks"]) == 0:
        return

    factiontid = faction_data["ID"]
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

    try:
        if guild.retal_config[str(faction.tid)]["channel"] in ("0", 0, None, ""):
            return
    except KeyError:
        return

    if last_attacks is None or last_attacks >= int(time.time()):
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
        elif (
            attack["modifiers"]["overseas"] == 1.25 and attack["modifiers"]["war"] == 1
        ):  # Overseas attack when not in war
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
                user is not None and user.battlescore != 0 and int(time.time()) - user.battlescore_update <= 259200
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
                                "value": commas(round(opponent_score)),
                                "inline": True,
                            },
                            {
                                "name": "Stat Score Update",
                                "value": f"<t:{int(time.time())}:R>",
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
                            "value": commas(stat.battlescore),
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
                    "footer": {"text": torn_timestamp()},
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

        if len(guild.retal_config[str(faction.tid)]["roles"]) != 0:
            for role in guild.retal_config[str(faction.tid)]["roles"]:
                if "content" not in payload:
                    payload["content"] = ""

                payload["content"] += f"<@&{role}>"

        try:
            discordpost.delay(
                f"channels/{guild.retal_config[str(faction.tid)]['channel']}/messages",
                payload=payload,
                channel=guild.retal_config[str(faction.tid)]["channel"],
            ).forget()
        except DiscordError as e:
            if e.code == 10003:
                logger.warning(
                    f"Unknown retal channel {guild.retal_config[str(faction.tid)]['channel']} in guild {guild.sid}"
                )
                return

            logger.exception(e)
            continue
        except Exception as e:
            logger.exception(e)
            continue


@celery.shared_task(name="tasks.faction.stat_db_attacks", routing_key="quick.stat_db_attacks", queue="quick")
def stat_db_attacks(faction_data, last_attacks=None):
    if len(faction_data) == 0:
        return
    elif "attacks" not in faction_data:
        return
    elif len(faction_data["attacks"]) == 0:
        return

    factiontid = faction_data["ID"]
    faction: FactionModel = FactionModel.objects(tid=factiontid).first()

    if faction is None:
        return
    elif faction.config.get("stats") in (0, None):
        return

    if last_attacks is None or last_attacks >= int(time.time()):
        last_attacks = faction.last_attacks

    attack: dict
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
                if user.battlescore_update - int(time.time()) <= 259200:  # Three days
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
                if user.battlescore_update - int(time.time()) <= 259200:  # Three days
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
            update_user.delay(tid=opponent_id, key=random.choice(faction.aa_keys)).forget()
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

    faction.last_attacks = list(faction_data["attacks"].values())[-1]["timestamp_ended"]
    faction.save()


@celery.shared_task(name="tasks.faction.oc_refresh", routing_key="quick.oc_refresh", queue="quick")
def oc_refresh():
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

        tornget.signature(
            kwargs={
                "endpoint": "faction/?selections=basic,crimes",
                "key": aa_key,
            },
            queue="api",
        ).apply_async(
            expires=300,
            link=oc_refresh_subtask.s(),
        )


@celery.shared_task(name="tasks.faction.oc_refresh_subtask", routing_key="default.oc_refresh_subtask", queue="default")
def oc_refresh_subtask(oc_data):
    faction: FactionModel = FactionModel.objects(tid=oc_data["ID"]).first()

    if faction is None:
        return

    guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

    if guild is None:
        return

    OC_DELAY = guild.oc_config[str(faction.tid)].get("delay", {"channel": 0, "roles": []}).get("channel") not in [
        None,
        0,
    ]
    OC_READY = guild.oc_config[str(faction.tid)].get("ready", {"channel": 0, "roles": []}).get("channel") not in [
        None,
        0,
    ]
    OC_INITIATED = guild.oc_config[str(faction.tid)].get("initiated", {"channel": 0}).get("channel") not in [None, 0]

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
            if OC_INITIATED:
                if oc_db.money_gain == 0 and oc_db.respect_gain == 0:
                    oc_status_str = "unsuccessfully"
                    oc_result_str = ""
                    oc_color = SKYNET_ERROR
                else:
                    oc_status_str = "successfully"
                    oc_result_str = (
                        f" resulting in a gain of ${commas(oc_db.money_gain)} and {commas(oc_db.respect_gain)} respect"
                    )
                    oc_color = SKYNET_GOOD

                initiator: typing.Optional[UserModel] = UserModel.objects(tid=oc_db.initiated_by).first()

                if initiator is None or initiator.name in (None, ""):
                    initiator_str = "Someone"
                else:
                    initiator_str = f"{initiator.name} [{initiator.tid}]"

                payload = {
                    "embeds": [
                        {
                            "title": f"OC of {faction.name} Initiated",
                            "description": f"{ORGANIZED_CRIMES[oc_data['crime_id']]} has been {oc_status_str} "
                            f"initiated by {initiator_str}{oc_result_str}.",
                            "color": oc_color,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": f"#{oc_db.ocid}"},
                        }
                    ],
                }

                try:
                    discordpost.delay(
                        f'channels/{guild.oc_config[str(faction.tid)]["initiated"]["channel"]}/messages',
                        payload=payload,
                        channel=guild.oc_config[str(faction.tid)]["initiated"]["channel"],
                    )
                except Exception as e:
                    logger.exception(e)
                    continue

            continue
        elif oc_db.time_ready > int(time.time()):
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
                        "color": SKYNET_ERROR,
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
                    channel=guild.oc_config[str(faction.tid)]["delay"]["channel"],
                ).forget()
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
                        "color": SKYNET_GOOD,
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
                    f'channels/{guild.oc_config[str(faction.tid)]["ready"]["channel"]}/messages',
                    payload=payload,
                    channel=guild.oc_config[str(faction.tid)]["ready"]["channel"],
                )
            except Exception as e:
                logger.exception(e)
                continue


@celery.shared_task(
    name="tasks.faction.auto_cancel_requests", routing_key="default.auto_cancel_requests", queue="default"
)
def auto_cancel_requests():
    withdrawal: WithdrawalModel
    for withdrawal in WithdrawalModel.objects(time_requested__gte=int(time.time()) - 7200):  # Two hours before now
        if int(time.time()) - withdrawal.time_requested < 3600:
            continue
        elif withdrawal.fulfiller != 0:
            continue

        withdrawal.fulfiller = -1
        withdrawal.time_fulfilled = int(time.time())
        withdrawal.save()

        requester: typing.Optional[UserModel] = UserModel.objects(tid=withdrawal.requester).first()

        if requester is None or requester.discord_id in (0, None, ""):
            continue

        faction: typing.Optional[FactionModel] = FactionModel.objects(tid=withdrawal.factiontid).first()
        server: typing.Optional[ServerModel] = ServerModel.objects(sid=faction.guild).first()

        try:
            if server is not None and str(faction.tid) in server.banking_config:
                discordpatch(
                    f"channels/{server.banking_config[str(faction.tid)]['channel']}/messages/{withdrawal.withdrawal_message}",
                    {
                        "embeds": [
                            {
                                "title": f"Vault Request #{withdrawal.wid}",
                                "description": "This request has timed-out and been automatically cancelled by the "
                                "system.",
                                "fields": [
                                    {
                                        "name": "Original Request Amount",
                                        "value": commas(withdrawal.amount),
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
                                "color": SKYNET_ERROR,
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
                                        "url": "https://www.torn.com/factions.php?step=your#/tab=controls&option="
                                        "give-to-user",
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
        except (DiscordError, NetworkingError):
            pass
        except Exception as e:
            logger.exception(e)

        try:
            dm_channel = discordpost("users/@me/channels", payload={"recipient_id": requester.discord_id})
        except (DiscordError, NetworkingError):
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
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        ).forget()
