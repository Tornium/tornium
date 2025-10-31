# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import inspect
import math
import random
import re
import time
import typing
import urllib.parse
import uuid
from decimal import DivisionByZero

from peewee import JOIN, DoesNotExist
from tornium_commons import with_db_connection
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.formatters import (
    LinkHTMLParser,
    commas,
    date_to_timestamp,
    timestamp,
    torn_timestamp,
)
from tornium_commons.models import (
    Faction,
    FactionPosition,
    Item,
    PersonalStats,
    Retaliation,
    Server,
    ServerAttackConfig,
    Stat,
    TornKey,
    User,
    Withdrawal,
)
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

import celery
from celery.utils.log import get_task_logger

from .api import discordpatch, discordpost, torn_stats_get, tornget
from .misc import send_dm
from .user import update_user

logger = get_task_logger("celery_app")

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


@celery.shared_task(
    name="tasks.faction.refresh_factions",
    routing_key="default.refresh_factions",
    queue="default",
    time_limit=30,
)
@with_db_connection
def refresh_factions():
    faction: Faction
    for faction in Faction.select().join(Server, JOIN.LEFT_OUTER):
        # Optimize this query to use one query to select valid factions

        if len(faction.aa_keys) == 0:
            continue

        tornget.signature(
            kwargs={
                "endpoint": "faction/?selections=basic,positions",
                "key": random.choice(faction.aa_keys),
            },
            queue="api",
        ).apply_async(expires=300, link=update_faction.s())

        ts_key = ""

        if faction.leader is not None and faction.leader.key not in ("", None):
            ts_key = faction.leader.key
        else:
            if faction.coleader is not None and faction.coleader.key not in ("", None):
                ts_key = faction.coleader.key

        if ts_key is not None:
            torn_stats_get.signature(
                kwargs={"endpoint": f"spy/faction/{faction.tid}", "key": ts_key},
                expires=300,
                link=update_faction_ts.s(),
            )

        try:
            if (
                faction.od_channel not in (None, 0)
                and faction.guild is not None
                and faction.tid in faction.guild.factions
            ):
                tornget.signature(
                    kwargs={
                        "endpoint": "faction/?selections=basic,contributors",
                        "stat": "drugoverdoses",
                        "key": random.choice(faction.aa_keys),
                    },
                    queue="api",
                ).apply_async(
                    expires=300,
                    link=check_faction_ods.s(),
                )
        except DoesNotExist:
            pass


@celery.shared_task(
    name="tasks.faction.update_faction",
    routing_key="quick.update_faction",
    queue="quick",
    time_limit=5,
)
@with_db_connection
def update_faction(faction_data):
    if faction_data is None:
        return
    elif faction_data.get("ID") is None:
        return  # Must include faction/basic

    Faction.insert(
        tid=faction_data["ID"],
        name=faction_data["name"],
        tag=str(faction_data["tag"]),  # Torn occasionally uses integers as tags
        respect=faction_data["respect"],
        capacity=faction_data["capacity"],
        leader=User.select().where(User.tid == faction_data["leader"]).first(),
        coleader=(
            User.select().where(User.tid == faction_data["co-leader"]).first()
            if faction_data["co-leader"] != 0
            else None
        ),
        last_members=datetime.datetime.utcnow(),
    ).on_conflict(
        conflict_target=[Faction.tid],
        preserve=[
            Faction.name,
            Faction.tag,
            Faction.respect,
            Faction.capacity,
            Faction.leader,
            Faction.coleader,
            Faction.last_members,
        ],
    ).execute()

    # faction/positions
    if "positions" in faction_data:
        positions_data = update_faction_positions(faction_data)

    users = [member_id for member_id in faction_data["members"].keys()]

    for member_id, member in faction_data["members"].items():
        # TODO: Switch upsert to bulk upsert
        if "positions" in faction_data:
            User.insert(
                tid=int(member_id),
                name=member["name"],
                level=member["level"],
                faction=faction_data["ID"],
                faction_aa=(positions_data[member["position"]]["aa"] if member["position"] is not None else False),
                faction_position=(
                    positions_data[member["position"]]["uuid"] if member["position"] is not None else None
                ),
                status=member["last_action"]["status"],
                last_action=datetime.datetime.fromtimestamp(
                    member["last_action"]["timestamp"], tz=datetime.timezone.utc
                ),
                last_refresh=datetime.datetime.utcnow(),
            ).on_conflict(
                conflict_target=[User.tid],
                preserve=[
                    User.name,
                    User.level,
                    User.faction,
                    User.faction_aa,
                    User.faction_position,
                    User.status,
                    User.last_action,
                    User.last_refresh,
                ],
            ).execute()
        else:
            User.insert(
                tid=member["player_id"],
                name=member["name"],
                level=member["level"],
                faction=faction_data["ID"],
                status=member["last_action"]["status"],
                last_action=datetime.datetime.fromtimestamp(
                    member["last_action"]["timestamp"], tz=datetime.timezone.utc
                ),
                last_refresh=datetime.datetime.utcnow(),
            ).on_conflict(
                conflict_target=[User.tid],
                preserve=[
                    User.name,
                    User.level,
                    User.faction,
                    User.status,
                    User.last_action,
                    User.last_refresh,
                ],
            ).execute()

    # Strips old faction members of their faction data
    User.update(faction=None, faction_position=None, faction_aa=False).where(
        (User.faction_id == faction_data["ID"]) & (User.tid.not_in(users))
    ).execute()


@celery.shared_task(
    name="tasks.faction.update_faction_positions",
    routing_key="quick.update_faction_positions",
    queue="quick",
    time_limit=5,
)
@with_db_connection
def update_faction_positions(faction_positions_data: dict) -> typing.Optional[dict]:
    if "positions" not in faction_positions_data or "ID" not in faction_positions_data:
        return None

    existing_positions = FactionPosition.select(FactionPosition.pid, FactionPosition.name).where(
        FactionPosition.faction_tid == faction_positions_data["ID"]
    )
    existing_position_names: typing.Set[str] = {position.name for position in existing_positions}

    latest_position_names: typing.Set[str] = {k for k in faction_positions_data["positions"]}

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

    deleted_position: FactionPosition
    for deleted_position in existing_positions.where(
        FactionPosition.name << (existing_position_names - latest_position_names)
    ):
        try:
            User.update(faction_position=None).where(User.faction_position_id == deleted_position.pid).execute()
            existing_positions.where(FactionPosition.name == deleted_position.name).get().delete_instance()
        except Exception as e:
            logger.exception(e)
            continue

        existing_position_names.remove(deleted_position.name)

    add_position_name: str
    for add_position_name in latest_position_names - existing_position_names:
        perms = faction_positions_data["positions"][add_position_name]
        pid = uuid.uuid4().hex

        FactionPosition.insert(
            pid=pid,
            name=add_position_name,
            faction_tid=faction_positions_data["ID"],
            default=bool(perms["default"]),
            use_medical_item=bool(perms["canUseMedicalItem"]),
            use_booster_item=bool(perms["canUseBoosterItem"]),
            use_drug_item=bool(perms["canUseDrugItem"]),
            use_energy_refill=bool(perms["canUseEnergyRefill"]),
            use_nerve_refill=bool(perms["canUseNerveRefill"]),
            loan_temporary_item=bool(perms["canLoanTemporaryItem"]),
            loan_weapon_armory=bool(perms["canLoanWeaponAndArmory"]),
            retrieve_loaned_armory=bool(perms["canRetrieveLoanedArmory"]),
            plan_init_oc=bool(perms.get("canPlanAndInitiateOrganisedCrime") or perms.get("canManageOC2") or False),
            access_fac_api=bool(perms["canAccessFactionApi"]),
            give_item=bool(perms["canGiveItem"]),
            give_money=bool(perms["canGiveMoney"]),
            give_points=bool(perms["canGivePoints"]),
            manage_forums=bool(perms["canManageForum"]),
            manage_applications=bool(perms["canManageApplications"]),
            kick_members=bool(perms["canKickMembers"]),
            adjust_balances=bool(perms["canAdjustMemberBalance"]),
            manage_wars=bool(perms["canManageWars"]),
            manage_upgrades=bool(perms["canManageUpgrades"]),
            send_newsletters=bool(perms["canSendNewsletter"]),
            change_announcement=bool(perms["canChangeAnnouncement"]),
            change_description=bool(perms["canChangeDescription"]),
        ).on_conflict(
            conflict_target=[FactionPosition.pid],
            preserve=[
                getattr(FactionPosition, p)
                for p in set(FactionPosition._meta.sorted_field_names) - {"pid", "name", "faction_tid"}
            ],
        ).execute()

        existing_position_names.add(add_position_name)
        positions_data[add_position_name] = {
            "uuid": pid,
            "aa": bool(perms["canAccessFactionApi"]),
        }

    modify_position_name: str
    for modify_position_name in existing_position_names & latest_position_names:
        perms = faction_positions_data["positions"][modify_position_name]
        existing_position: typing.Optional[FactionPosition] = existing_positions.where(
            FactionPosition.name == modify_position_name
        ).first()

        if existing_position is None:
            continue

        FactionPosition.insert(
            pid=existing_position.pid,
            name=modify_position_name,
            faction_tid=faction_positions_data["ID"],
            default=bool(perms["default"]),
            use_medical_item=bool(perms["canUseMedicalItem"]),
            use_booster_item=bool(perms["canUseBoosterItem"]),
            use_drug_item=bool(perms["canUseDrugItem"]),
            use_energy_refill=bool(perms["canUseEnergyRefill"]),
            use_nerve_refill=bool(perms["canUseNerveRefill"]),
            loan_temporary_item=bool(perms["canLoanTemporaryItem"]),
            loan_weapon_armory=bool(perms["canLoanWeaponAndArmory"]),
            retrieve_loaned_armory=bool(perms["canRetrieveLoanedArmory"]),
            plan_init_oc=bool(perms.get("canPlanAndInitiateOrganisedCrime") or perms.get("canManageOC2") or False),
            access_fac_api=bool(perms["canAccessFactionApi"]),
            give_item=bool(perms["canGiveItem"]),
            give_money=bool(perms["canGiveMoney"]),
            give_points=bool(perms["canGivePoints"]),
            manage_forums=bool(perms["canManageForum"]),
            manage_applications=bool(perms["canManageApplications"]),
            kick_members=bool(perms["canKickMembers"]),
            adjust_balances=bool(perms["canAdjustMemberBalance"]),
            manage_wars=bool(perms["canManageWars"]),
            manage_upgrades=bool(perms["canManageUpgrades"]),
            send_newsletters=bool(perms["canSendNewsletter"]),
            change_announcement=bool(perms["canChangeAnnouncement"]),
            change_description=bool(perms["canChangeDescription"]),
        ).on_conflict(
            conflict_target=[FactionPosition.pid],
            preserve=[
                getattr(FactionPosition, p)
                for p in set(FactionPosition._meta.sorted_field_names) - {"pid", "name", "faction_tid"}
            ],
        ).execute()

        positions_data[modify_position_name] = {
            "uuid": existing_position.pid,
            "aa": bool(perms["canAccessFactionApi"]),
        }

    return positions_data


@celery.shared_task(
    name="tasks.faction.update_faction_ts",
    routing_key="default.update_faction_ts",
    queue="default",
    time_limit=5,
)
@with_db_connection
def update_faction_ts(faction_ts_data):
    if not faction_ts_data["status"]:
        return

    for user_id, user_data in faction_ts_data["faction"]["members"].items():
        if "spy" not in user_data:
            continue

        try:
            user: User = User.select().where(User.tid == int(user_id)).get()
        except DoesNotExist:
            continue

        if user.key is not None:
            continue
        elif user.battlescore_update is not None and user_data["spy"]["timestamp"] <= timestamp(
            user.battlescore_update
        ):
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
        user.battlescore_update = datetime.datetime.fromtimestamp(
            user_data["spy"]["timestamp"], tz=datetime.timezone.utc
        )
        user.save()


@celery.shared_task(
    name="tasks.faction.check_faction_ods",
    routing_key="quick.check_faction_ods",
    queue="quick",
    time_limit=5,
)
@with_db_connection
def check_faction_ods(faction_od_data):
    try:
        faction: Faction = (
            Faction.select(
                Faction.tid,
                Faction.name,
                Faction.od_data,
                Faction.od_channel,
                Faction.guild,
            )
            .join(Server, JOIN.LEFT_OUTER)
            .where(Faction.tid == faction_od_data["ID"])
            .get()
        )
    except (KeyError, DoesNotExist):
        return

    if faction.od_data is None or len(faction.od_data) == 0:
        Faction.update(od_data=faction_od_data["contributors"]["drugoverdoses"]).where(
            Faction.tid == faction_od_data["ID"]
        ).execute()
        return
    elif faction.od_channel in (0, None):
        return
    elif faction.tid not in faction.guild.factions:
        return

    for tid, user_od in faction_od_data["contributors"]["drugoverdoses"].items():
        if faction.od_data.get(tid) is None and user_od["contributed"] > 0:
            overdosed_user: typing.Optional[User] = User.select(User.name).where(User.tid == tid).first()
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
        elif faction.od_data.get(tid) is not None and user_od["contributed"] != faction.od_data.get(tid).get(
            "contributed"
        ):
            overdosed_user: typing.Optional[User] = User.select(User.name).where(User.tid == tid).first()
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

    faction.od_data = faction_od_data["contributors"]["drugoverdoses"]
    faction.save()


@celery.shared_task(
    name="tasks.faction.fetch_attacks_runner",
    routing_key="default.fetch_attacks_runner",
    queue="default",
    time_limit=15,
)
@with_db_connection
def fetch_attacks_runner():
    for api_key in (
        TornKey.select().distinct(TornKey.user.faction.tid).join(User).join(Faction).where(TornKey.default == True)
    ):
        if api_key.user.faction is None:
            continue

        faction: typing.Optional[Faction] = Faction.select().where(Faction.tid == api_key.user.faction.tid).first()

        if faction is None:
            continue
        elif len(faction.aa_keys) == 0:
            continue
        elif faction.last_attacks is None or timestamp(faction.last_attacks) == 0:
            # TODO: Convert to an atomic update
            faction.last_attacks = datetime.datetime.utcnow()
            faction.save()
            continue
        elif time.time() - timestamp(faction.last_attacks) > 86401:  # One day
            # Prevents old data from being added (especially for retals)
            # TODO: Convert to an atomic update
            faction.last_attacks = datetime.datetime.utcnow()
            faction.save()
            continue

        last_attacks: int = timestamp(faction.last_attacks)

        tornget.signature(
            kwargs={
                "endpoint": "faction/?selections=basic,attacks",
                "key": random.choice(faction.aa_keys),
            },
            queue="api",
        ).apply_async(
            expires=300,
            link=celery.group(
                check_attacks.signature(
                    kwargs={"last_attacks": int(last_attacks)},
                    queue="quick",
                ),
                stat_db_attacks.signature(
                    kwargs={"last_attacks": int(last_attacks)},
                    queue="quick",
                ),
            ),
        )

    retal: Retaliation
    for retal in Retaliation.select().where(
        (Retaliation.attack_ended <= (datetime.datetime.utcnow() - datetime.timedelta(minutes=5)))
        & (Retaliation.channel_id.is_null(False))
        & (Retaliation.message_id.is_null(False))
    ):
        # Runs at 6 minutes after to allow API calls to be made if the attack is made close to timeout
        # TODO: Convert to a delete returning query
        try:
            discordpatch.delay(
                f"channels/{retal.channel_id}/messages/{retal.message_id}",
                {
                    "embeds": [
                        {
                            "title": f"Retal Timeout for {retal.defender.faction.name}",
                            "description": (
                                f"{retal.attacker.user_str_self()} of "
                                f"{'N/A' if retal.attacker.faction is None else retal.attacker.faction.name} has attacked "
                                f"{retal.defender.user_str_self()}, but the retaliation timed out "
                                f"<t:{int(timestamp(retal.attack_ended) + 300)}:R>"
                            ),
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "components": [],
                },
            ).forget()
        except Exception as e:
            logger.exception(e)
            continue

    Retaliation.delete().where(
        Retaliation.attack_ended <= (datetime.datetime.utcnow() - datetime.timedelta(minutes=6))
    ).execute()


@celery.shared_task(
    name="tasks.faction.stat_db_attacks",
    routing_key="quick.stat_db_attacks",
    queue="quick",
    time_limit=5,
)
@with_db_connection
def stat_db_attacks(faction_data: dict, last_attacks: int):
    if len(faction_data.get("attacks", [])) == 0:
        return

    try:
        faction: Faction = Faction.select().where(Faction.tid == faction_data["ID"]).get()
    except (KeyError, DoesNotExist):
        return

    new_last_attacks = last_attacks
    for attack in faction_data["attacks"].values():
        if attack["timestamp_ended"] > new_last_attacks:
            new_last_attacks = attack["timestamp_ended"]

    Faction.update(
        last_attacks=datetime.datetime.fromtimestamp(
            new_last_attacks,
            tz=datetime.timezone.utc,
        )
    ).where(Faction.tid == faction_data["ID"]).execute()

    if not faction.stats_db_enabled:
        return

    attack: dict
    for attack in faction_data["attacks"].values():
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
        elif attack["timestamp_ended"] <= last_attacks + 1:
            continue

        # User: faction member
        # Opponent: non-faction member regardless of attack or defend

        if attack["defender_faction"] == faction_data["ID"]:  # Defender fac is the fac making the call
            if attack["attacker_id"] in ("", 0):  # Attacker stealthed
                continue
            elif attack["respect"] == 0:  # Attack by fac member
                continue

            user: typing.Optional[User] = (
                User.select(User.battlescore, User.battlescore_update, User.faction)
                .where(User.tid == attack["defender_id"])
                .first()
            )

            if user is None or user.battlescore in (None, 0):
                continue
            elif (
                user.battlescore_update is None or int(time.time()) - timestamp(user.battlescore_update) > 259200
            ):  # Three days
                continue

            opponent_id = attack["attacker_id"]

            if attack["attacker_faction"] != 0:
                Faction.insert(
                    tid=attack["attacker_faction"],
                    name=attack["attacker_factionname"],
                ).on_conflict(
                    conflict_target=[Faction.tid],
                    preserve=[Faction.name],
                ).execute()

            User.insert(
                tid=attack["attacker_id"],
                name=attack["attacker_name"],
                faction=(attack["attacker_faction"] if attack["attacker_faction"] != 0 else None),
            ).on_conflict(
                conflict_target=[User.tid],
                preserve=[User.name, User.faction],
            ).execute()
        else:  # User is the attacker
            user: typing.Optional[User] = (
                User.select(User.battlescore, User.battlescore_update, User.faction)
                .where(User.tid == attack["attacker_id"])
                .first()
            )

            if user is None or user.battlescore in (None, 0):
                continue
            elif (
                user.battlescore_update is None or int(time.time()) - timestamp(user.battlescore_update) > 259200
            ):  # Three days
                continue

            opponent_id = attack["defender_id"]

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
                faction=(attack["defender_faction"] if attack["defender_faction"] != 0 else None),
            ).on_conflict(
                conflict_target=[User.tid],
                preserve=[User.name, User.faction],
            ).execute()

        try:
            update_user.delay(tid=opponent_id, key=random.choice(faction.aa_keys)).forget()
        except Exception as e:
            logger.exception(e)
            continue

        try:
            if attack["defender_faction"] == faction_data["ID"]:
                opponent_score = user.battlescore / ((attack["modifiers"]["fair_fight"] - 1) * 0.375)
            else:
                opponent_score = (attack["modifiers"]["fair_fight"] - 1) * 0.375 * user.battlescore
        except DivisionByZero:
            continue

        if opponent_score == 0:
            continue

        if (
            Stat.select()
            .where(
                (Stat.tid == opponent_id)
                & (
                    Stat.time_added
                    == datetime.datetime.fromtimestamp(attack["timestamp_ended"], tz=datetime.timezone.utc)
                )
                & (Stat.added_group == (0 if faction.stats_db_global else user.faction_id))
            )
            .exists()
        ):
            continue

        try:
            Stat.create(
                tid=opponent_id,
                battlescore=opponent_score,
                time_added=datetime.datetime.fromtimestamp(attack["timestamp_ended"], tz=datetime.timezone.utc),
                added_group=0 if faction.stats_db_global else user.faction_id,
            )
        except Exception as e:
            logger.exception(e)
            continue


def validate_attack_retaliation(attack: dict, faction: Faction) -> bool:
    """
    Validate that the attack is a valid attack that would have completed a retaliation

    Args:
        attack: dict
            Torn attack data
        faction: Faction
            Faction model for the faction this job is running for

    Returns:
        retaliation: bool
            Whether the attack was a valid retaliation
    """

    if attack["result"] != "Hospitalized":
        return False
    elif attack["attacker_faction"] != faction.tid:
        # Attack was not an outgoing attack/defend
        return False
    elif attack["modifiers"]["retaliation"] == 1:
        return False

    return True


def validate_attack_available_retaliation(attack: dict, faction: Faction) -> bool:
    """
    Validate that the attack is a valid attack that can be retaliated for

    Args:
        attack: dict
            Torn attack data
        faction: Faction
            Faction model for the faction this job is running for

    Returns:
        retaliation: bool
            Whether this attack is a valid attack that can be retaliated
    """

    if attack["defender_faction"] != faction.tid:
        # Attack was an outgoing attack
        return False
    elif attack["attacker_id"] in ("", 0):
        # Attacker was stealthed
        return False
    elif attack["respect"] == 0:
        # Attacker was a member of the defender's faction or was a recruit in any faction
        return False
    elif attack["modifiers"]["overseas"] == 1.25 and attack["modifiers"]["war"] == 1:
        # Overseas attack when not in war
        return False
    elif int(time.time()) - attack["timestamp_ended"] >= 300:
        return False
    elif Retaliation.select().where(Retaliation.attack_code == attack["code"]).exists():
        return False

    return True


def generate_retaliation_embed(
    attack: dict,
    faction: Faction,
    attack_config: ServerAttackConfig,
    faction_data: dict,
) -> dict:
    user: User
    try:
        user = (
            User.select(
                User.tid,
                User.name,
                User.battlescore,
                User.battlescore_update,
                User.faction,
            )
            .where(User.tid == attack["defender_id"])
            .get()
        )
    except DoesNotExist:
        user = User.create(
            tid=attack["defender_id"],
            name=attack["defender_name"],
            faction=attack["defender_faction"],
        )

    opponent: User
    try:
        opponent: typing.Optional[User] = (
            User.select(
                User.tid,
                User.name,
            )
            .where(User.tid == attack["attacker_id"])
            .get()
        )
    except DoesNotExist:
        # It is assumed that the attacker is in a faction
        Faction.insert(tid=attack["attacker_faction"], name=attack["attacker_factionname"]).on_conflict_ignore()
        opponent = User.create(
            tid=attack["attacker_id"],
            name=attack["attacker_name"],
            faction=attack["attacker_faction"],
        )

    opponents_personal_stats: typing.Optional[PersonalStats] = (
        PersonalStats.select(
            PersonalStats.xantaken,
            PersonalStats.useractivity,
            PersonalStats.elo,
            PersonalStats.statenhancersused,
            PersonalStats.energydrinkused,
            PersonalStats.booksread,
            PersonalStats.attackswon,
            PersonalStats.respectforfaction,
            PersonalStats.timestamp,
        )
        .where(PersonalStats.user == attack["attacker_id"])
        .first()
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
            user is not None
            and user.battlescore != 0
            and user.battlescore_update is not None
            and int(time.time()) - timestamp(user.battlescore_update) <= 259200
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
        stat: typing.Optional[Stat]
        try:
            if user is not None and user.faction_id is not None:
                stat = (
                    Stat.select()
                    .where(
                        (Stat.tid == opponent.tid) & ((Stat.added_group == 0) | (Stat.added_group == user.faction_id))
                    )
                    .order_by(Stat.time_added)
                    .first()
                )
            else:
                stat = (
                    Stat.select()
                    .where((Stat.tid == opponent.tid) & (Stat.added_group == 0))
                    .order_by(Stat.time_added)
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
                        "value": commas(stat.battlescore),
                        "inline": True,
                    },
                    {
                        "name": "Stat Score Update",
                        "value": f"<t:{int(timestamp(stat.time_added))}:R>",
                        "inline": True,
                    },
                )
            )

    if attack["attacker_faction"] not in (0, ""):
        fields.append(
            {
                "name": "Opponent Faction Chaining",
                "value": f"{attack['chain'] > 10} ({commas(attack['chain'])})",
                "inline": False,
            }
        )

    if attack["modifiers"]["retaliation"] != 1:
        fields.append(
            {
                "name": "Is Retaliation",
                "value": "True",
                "inline": False,
            }
        )

    if attack["modifiers"]["overseas"] != 1:
        fields.append(
            {
                "name": "Overseas Hit",
                "value": f"True ({faction_data['members'][str(attack['defender_id'])]['status']['description'][3:]})",
                "inline": False,
            }
        )

    if (
        opponents_personal_stats is not None
        and int(time.time()) - date_to_timestamp(opponents_personal_stats.timestamp) <= 604800
    ):  # One week
        fields.append(
            {
                "name": "Personal Stats",
                "value": inspect.cleandoc(
                    f"""Xanax Used: {commas(opponents_personal_stats.xantaken)}
                    SEs Used: {commas(opponents_personal_stats.statenhancersused)}
                    E-Cans Used: {commas(opponents_personal_stats.energydrinkused)}
                    Books Read: {commas(opponents_personal_stats.booksread)}

                    ELO: {commas(opponents_personal_stats.elo)}
                    Average Respect: {commas(opponents_personal_stats.respectforfaction / opponents_personal_stats.attackswon, stock_price=True)}
                    """
                ),
            }
        )

    payload = {
        "embeds": [
            {
                "title": title,
                "description": f"{opponent.name} [{opponent.tid}] {attack['result'].lower()} {user.name} "
                f"[{user.tid}] (-{attack['respect_loss']})",
                "fields": fields,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "footer": {"text": torn_timestamp(attack["timestamp_ended"])},
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

    for role in attack_config.retal_roles:
        if "content" not in payload:
            payload["content"] = ""

        payload["content"] += f"<@&{role}>"

    return payload


def validate_attack_bonus(attack: dict, faction: Faction, attack_config: ServerAttackConfig) -> bool:
    if attack["attacker_faction"] == faction.tid:
        return False
    elif attack["chain"] not in (
        100,
        250,
        500,
        1_000,
        2_500,
        5_000,
        10_000,
        25_000,
        50_000,
        100_000,
    ):
        return False
    elif attack_config.chain_bonus_length is None:
        return False
    elif attack["chain"] < attack_config.chain_bonus_length:
        return False

    return True


@celery.shared_task(
    name="tasks.faction.check_attacks",
    routing_key="quick.check_attacks",
    queue="quick",
    time_limit=10,
)
@with_db_connection
def check_attacks(faction_data: dict, last_attacks: int):
    if len(faction_data.get("attacks", [])) == 0:
        return

    try:
        # TODO: Limit selected fields
        faction: Faction = Faction.select().join(Server).where(Faction.tid == faction_data["ID"]).get()
    except (KeyError, DoesNotExist):
        return

    if faction.guild is None:
        return
    elif faction.tid not in faction.guild.factions:
        return

    try:
        attack_config: ServerAttackConfig = (
            ServerAttackConfig.select(
                ServerAttackConfig.retal_roles,
                ServerAttackConfig.retal_channel,
                ServerAttackConfig.retal_wars,
                ServerAttackConfig.chain_bonus_channel,
                ServerAttackConfig.chain_bonus_roles,
                ServerAttackConfig.chain_alert_channel,
                ServerAttackConfig.chain_alert_roles,
                ServerAttackConfig.chain_alert_minimum,
            )
            .where((ServerAttackConfig.server == faction.guild_id) & (ServerAttackConfig.faction == faction.tid))
            .get()
        )
    except DoesNotExist:
        ALERT_RETALS = False
        ALERT_CHAIN_BONUS = False
        ALERT_CHAIN_ALERT = False
    else:
        ALERT_RETALS = attack_config.retal_channel not in (None, 0)
        ALERT_CHAIN_BONUS = attack_config.chain_bonus_channel not in (None, 0)
        ALERT_CHAIN_ALERT = attack_config.chain_alert_channel not in (None, 0)

    possible_retals = {}
    latest_outgoing_attack: typing.Optional[typing.Tuple[int, int]] = None

    for attack in faction_data["attacks"].values():
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

        if attack["attacker_faction"] == faction.tid and (
            latest_outgoing_attack is None or latest_outgoing_attack[0] < attack["timestamp_ended"]
        ):
            # Used to determine the last successful outgoing attack by the faction
            latest_outgoing_attack = (attack["timestamp_ended"], attack["chain"])

        if attack["timestamp_ended"] <= last_attacks + 1:
            continue

        if ALERT_RETALS and validate_attack_retaliation(attack, faction):
            # TODO: Check possible_retals if the retaliation attack data is in the same API response as the original attack

            retal: Retaliation
            for retal in (
                Retaliation.delete()
                .where(
                    (Retaliation.attacker == attack["defender_id"])
                    & (Retaliation.defender << (User.select().where(User.faction == attack["attacker_faction"])))
                    & (Retaliation.channel_id.is_null(False))
                    & (Retaliation.message_id.is_null(False))
                )
                .returning(Retaliation.channel_id, Retaliation.message_id)
            ):
                discordpatch.delay(
                    f"channels/{retal.channel_id}/messages/{retal.message_id}",
                    {
                        "embeds": [
                            {
                                "title": f"Retal Completed for {faction.name}",
                                "description": (
                                    f"{attack['attacker_name']} [{attack['attacker_id']}] hospitalized {attack['defender_name']} [{attack['defender_id']}] (+{attack['respect_gain']})."
                                ),
                                "color": SKYNET_GOOD,
                            }
                        ],
                        "components": [],
                    },
                ).forget()
        elif (
            ALERT_RETALS
            and validate_attack_available_retaliation(attack, faction)
            and (attack_config.retal_wars or attack["modifiers"]["war"] == 1)
        ):
            try:
                possible_retals[attack["code"]] = {
                    "task": discordpost.delay(
                        f"channels/{attack_config.retal_channel}/messages",
                        payload=generate_retaliation_embed(attack, faction, attack_config, faction_data),
                    ),
                    **attack,
                }
            except Exception as e:
                logger.exception(e)
                pass
        elif validate_attack_available_retaliation(attack, faction):
            possible_retals[attack["code"]] = {"task": None, **attack}

        # Check for bonuses dropped upon this faction
        if ALERT_CHAIN_BONUS and validate_attack_bonus(attack, faction, attack_config):
            if attack["attacker_id"] in (0, ""):
                attacker_str = "an unknown attacker and faction"
            else:
                attacker_str = f"{attack['attacker_factionname']} [{attack['attacker_faction']}] (through {attack['attacker_name']} [{attack['attacker_id']}])"

            payload = {
                "embeds": [
                    {
                        "title": f"Bonus Dropped Upon {faction.name} [{faction.tid}]",
                        "description": f"A {commas(attack['chain'])} bonus hit was dropped upon {faction.name} [{faction.tid}] by {attacker_str} causing a loss of {commas(attack['respect_loss'])} respect.",
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
                                "label": "Attack Log",
                                "url": f"https://www.torn.com/loader.php?sid=attackLog&ID={attack['code']}",
                            },
                        ],
                    }
                ],
            }

            if attack["attacker_id"] not in (0, ""):
                payload["components"][0]["components"].append(
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Attacking Faction",
                        "url": f"https://www.torn.com/factions.php?step=profile&ID={attack['attacker_faction']}",
                    }
                )

            for role in attack_config.chain_bonus_roles:
                if "content" not in payload:
                    payload["content"] = ""

                payload["content"] += f"<@&{role}>"

            discordpost.delay(
                f"channels/{attack_config.chain_bonus_channel}/messages",
                payload=payload,
            ).forget()

    if (
        latest_outgoing_attack is not None
        and ALERT_CHAIN_ALERT
        and int(time.time()) - latest_outgoing_attack[0] >= 300 - attack_config.chain_alert_minimum
        and int(time.time()) - latest_outgoing_attack[0] < 300
        and latest_outgoing_attack[1] >= 100
    ):
        payload = {
            "content": "Chain alert!! ",
            "embeds": [
                {
                    "title": "Chain Timer Alert",
                    "description": f"The chain timer for {faction.name} [{faction.tid}] has dropped below one minute and will reach zero <t:{latest_outgoing_attack[0] + 300}:R> with a current chain length of {commas(latest_outgoing_attack[1])}.",
                    "color": SKYNET_ERROR,
                }
            ],
            "components": [],
        }

        for role in attack_config.chain_alert_roles:
            if "content" not in payload:
                payload["content"] = ""

            payload["content"] += f"<@&{role}>"

        discordpost.delay(f"channels/{attack_config.chain_alert_channel}/messages", payload=payload).forget()

    for retal in possible_retals.values():
        retal["task"]: typing.Optional[celery.result.AsyncResult]
        try:
            message = retal["task"].get(disable_sync_subtasks=False)
            message_id = message["id"]
            channel_id = message["channel_id"]
        except Exception:
            message_id = None
            channel_id = None

        Retaliation.insert(
            attack_code=retal["code"],
            attack_ended=datetime.datetime.fromtimestamp(retal["timestamp_ended"], tz=datetime.timezone.utc),
            defender=retal["defender_id"],
            attacker=retal["attacker_id"],
            message_id=message_id,
            channel_id=channel_id,
        ).on_conflict_ignore().execute()


@celery.shared_task(
    name="tasks.faction.auto_cancel_requests",
    routing_key="default.auto_cancel_requests",
    queue="default",
    time_limit=5,
)
@with_db_connection
def auto_cancel_requests():
    faction_withdrawals: typing.Dict[int, typing.List[int]] = {}

    withdrawal: Withdrawal
    for withdrawal in Withdrawal.select().where(
        (Withdrawal.status == 1)
        & (Withdrawal.time_fulfilled >= datetime.datetime.utcnow() - datetime.timedelta(minutes=11))
        & (Withdrawal.time_fulfilled <= datetime.datetime.utcnow() - datetime.timedelta(minutes=1))
    ):
        # Fulfilled requests that were fulfilled between 1 and 11 minutes before now
        faction_withdrawals.setdefault(withdrawal.faction_tid, []).append(withdrawal.wid)

    for faction_tid, withdrawals in faction_withdrawals.items():
        try:
            faction: Faction = Faction.select().where(Faction.tid == faction_tid).get()
        except DoesNotExist:
            continue

        if len(faction.aa_keys) == 0:
            continue

        tornget.signature(
            kwargs={
                "endpoint": "faction/?selections=fundsnews,basic",
                "key": random.choice(faction.aa_keys),
                "pass_error": True,
            },
            queue="api",
        ).apply_async(
            expires=300,
            link=verify_faction_withdrawals.signature(kwargs={"withdrawals": withdrawals}),
        )

    withdrawal: Withdrawal
    for withdrawal in Withdrawal.select().where(
        (Withdrawal.status == 0)
        & (Withdrawal.expires_at.is_null(False))
        & (Withdrawal.expires_at <= datetime.datetime.utcnow())
    ):  # One hour before now
        Withdrawal.update(status=3, time_fulfilled=datetime.datetime.utcnow()).where(
            Withdrawal.wid == withdrawal.wid
        ).execute()

        requester: typing.Optional[User] = (
            User.select(User.name, User.tid, User.discord_id).where(User.tid == withdrawal.requester).first()
        )

        if requester is None or requester.discord_id in (0, None):
            continue

        try:
            faction: Faction = (
                Faction.select(Faction.tid, Faction.guild)
                .join(Server, JOIN.LEFT_OUTER)
                .where(Faction.tid == withdrawal.faction_tid)
                .first()
            )
        except DoesNotExist:
            continue

        try:
            if faction.guild is not None and str(faction.tid) in faction.guild.banking_config:
                discordpatch.delay(
                    f"channels/{faction.guild.banking_config[str(faction.tid)]['channel']}/messages/{withdrawal.withdrawal_message}",
                    {
                        "embeds": [
                            {
                                "title": f"Vault Request #{withdrawal.wid}",
                                "description": "This request has timed-out and been automatically cancelled by the "
                                "system.",
                                "fields": [
                                    {
                                        "name": "Original Request Amount",
                                        "value": f"{commas(withdrawal.amount)} {'Cash' if withdrawal.cash_request else 'Points'}",
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
                        "components": [],
                    },
                )
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


@celery.shared_task(
    name="tasks.faction.verify_faction_withdrawals",
    routing_key="quick.verify_faction_withdrawals",
    queue="quick",
    time_limit=5,
)
@with_db_connection
def verify_faction_withdrawals(funds_news: dict, withdrawals):
    faction_tid = funds_news["ID"]
    missing_fulfillments: typing.List[Withdrawal] = [
        w for w in Withdrawal.select().where(Withdrawal.wid << list(withdrawals)) if w is not None
    ]

    if "error" in funds_news:
        for withdrawal in missing_fulfillments:
            try:
                requester_discord_id = User.user_discord_id(withdrawal.requester)
            except DoesNotExist:
                continue

            send_dm(
                requester_discord_id,
                payload={
                    "embeds": [
                        {
                            "title": "Vault Request Unknown Status",
                            "description": (
                                f"Your vault request #{withdrawal.wid} may not have been fulfilled after being marked as fulfilled by "
                                f"{'Someone' if withdrawal.fulfiller == -1 else User.user_str(withdrawal.fulfiller)} due to an "
                                f"error with the Torn API. If you didn't receive the {'money' if withdrawal.cash_request else 'points'}, "
                                f"please redo the vault request for {'$' + commas(withdrawal.amount) if withdrawal.cash_request else commas(withdrawal.amount) + ' points'}."
                            ),
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            )
        return

    for fund_action in funds_news.get("fundsnews", {}).values():
        if "was given" not in fund_action["news"]:
            continue

        money_sent = "$" in fund_action["news"]
        requester_html, fulfiller_html = re.findall(r"(<a.+?</a>)", fund_action["news"])

        requester_parser = LinkHTMLParser()
        fulfiller_parser = LinkHTMLParser()
        requester_parser.feed(requester_html)
        fulfiller_parser.feed(fulfiller_html)

        try:
            requester = urllib.parse.parse_qs(urllib.parse.urlparse(requester_parser.href).query).get("XID")[0]
            fulfiller = urllib.parse.parse_qs(urllib.parse.urlparse(fulfiller_parser.href).query).get("XID")[0]
        except IndexError:
            continue

        if requester is None or fulfiller is None:
            continue

        value = re.search(
            (r"</a> was given \$(.+?) by <a" if money_sent else r"</a> was given (.+?) points by <a"),
            fund_action["news"],
        ).groups()

        try:
            value = int("".join(value[0].split(",")))
        except (TypeError, ValueError, IndexError):
            continue

        withdrawal: Withdrawal
        for withdrawal in missing_fulfillments:
            update_kwargs = {}

            if withdrawal.requester != int(requester):
                continue
            elif withdrawal.cash_request != money_sent:
                continue
            elif withdrawal.amount != value:
                continue
            elif withdrawal.time_requested.replace(tzinfo=datetime.timezone.utc) >= datetime.datetime.fromtimestamp(
                fund_action["timestamp"], tz=datetime.timezone.utc
            ):
                continue
            elif withdrawal.fulfiller != int(fulfiller):
                update_kwargs["fulfiller"] = int(fulfiller)

            update_kwargs["time_fulfilled"] = datetime.datetime.fromtimestamp(
                fund_action["timestamp"], tz=datetime.timezone.utc
            )
            Withdrawal.update(**update_kwargs).where(Withdrawal.wid == withdrawal.wid).execute()

            missing_fulfillments.remove(withdrawal)
            break

    if len(missing_fulfillments) == 0:
        return

    try:
        faction = Faction.select().where(Faction.tid == faction_tid).get()
    except DoesNotExist:
        return

    for withdrawal in missing_fulfillments:
        try:
            if faction.guild is not None and str(faction.tid) in faction.guild.banking_config:
                discordpatch.delay(
                    f"channels/{faction.guild.banking_config[str(faction.tid)]['channel']}/messages/{withdrawal.withdrawal_message}",
                    {
                        "embeds": [
                            {
                                "title": f"Vault Request #{withdrawal.wid}",
                                "description": f"This request has been marked as fulfilled by {'Someone' if withdrawal.fulfiller == -1 else User.user_str(withdrawal.fulfiller)} but no subsequent action could be found in the faction logs.",
                                "fields": [
                                    {
                                        "name": "Original Request Amount",
                                        "value": f"{commas(withdrawal.amount)} {'Cash' if withdrawal.cash_request else 'Points'}",
                                    },
                                    {
                                        "name": "Original Requester",
                                        "value": User.user_str(withdrawal.requester),
                                    },
                                ],
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "color": SKYNET_ERROR,
                            }
                        ],
                        "components": [],
                    },
                )
        except Exception as e:
            logger.exception(e)

        try:
            requester_discord_id = User.user_discord_id(withdrawal.requester)
        except DoesNotExist:
            continue

        send_dm(
            requester_discord_id,
            payload={
                "embeds": [
                    {
                        "title": "Vault Request Not Fulfilled",
                        "description": (
                            f"Your vault request #{withdrawal.wid} may not have been fulfilled after being marked as fulfilled by "
                            f"{'Someone' if withdrawal.fulfiller == -1 else User.user_str(withdrawal.fulfiller)} but no subsequent "
                            f"action could be found in the faction logs. If you didn't receive the "
                            f"{'money' if withdrawal.cash_request else 'points'}, please redo the vault request for "
                            f"{'$' + commas(withdrawal.amount) if withdrawal.cash_request else commas(withdrawal.amount) + ' points'}."
                        ),
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "color": SKYNET_ERROR,
                    }
                ]
            },
        )


@celery.shared_task(
    name="tasks.faction.armory_check",
    routing_key="quick.armory_check",
    queue="quick",
    time_limit=5,
)
@with_db_connection
def armory_check():
    for api_key in (
        TornKey.select()
        .distinct(TornKey.user.faction.tid)
        .join(User)
        .join(Faction)
        .where((TornKey.default == True) & (TornKey.user.faction_aa == True))
    ):
        faction: typing.Optional[Faction] = Faction.select().where(Faction.tid == api_key.user.faction_id).first()

        if faction is None:
            continue
        elif len(faction.aa_keys) == 0:
            continue
        try:
            if faction.guild is None:
                continue
        except DoesNotExist:
            continue

        if faction.tid not in faction.guild.factions:
            continue
        elif not faction.guild.armory_enabled:
            continue
        elif str(faction.tid) not in faction.guild.armory_config:
            continue
        elif not faction.guild.armory_config[str(faction.tid)].get("enabled", False):
            continue
        elif faction.guild.armory_config[str(faction.tid)].get("channel", 0) == 0:
            continue
        elif len(faction.guild.armory_config[str(faction.tid)].get("items", {})) == 0:
            continue

        tornget.signature(
            kwargs={
                "endpoint": "faction/?selections=armor,boosters,drugs,medical,temporary,weapons",
                "key": random.choice(faction.aa_keys),
            },
            queue="api",
        ).apply_async(
            expires=300,
            link=armory_check_subtask.signature(
                kwargs={
                    "faction_id": faction.tid,
                },
                queue="quick",
            ),
        )


@celery.shared_task(
    name="tasks.faction.armory_check_subtask",
    routing_key="quick.armory_check_subtask",
    queue="quick",
    time_limit=5,
)
@with_db_connection
def armory_check_subtask(_armory_data, faction_id: int):
    try:
        faction: Faction = Faction.select().where(Faction.tid == faction_id).get()
    except DoesNotExist:
        return

    if faction.guild is None:
        return
    elif faction.tid not in faction.guild.factions:
        return
    elif not faction.guild.armory_enabled:
        return
    elif str(faction.tid) not in faction.guild.armory_config:
        return

    faction_config = faction.guild.armory_config[str(faction.tid)]

    if not faction_config.get("enabled", False):
        return
    elif faction_config.get("channel", 0) == 0:
        return
    elif len(faction_config.get("items", {})) == 0:
        return

    payload = {
        "content": "".join([f"<@&{role}>" for role in faction_config.get("roles", [])]),
        "embeds": [],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Armory",
                        "url": "https://www.torn.com/factions.php?step=your&type=1#/tab=armoury",
                    },
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Item Market",
                        "url": "https://www.torn.com/imarket.php",
                    },
                ],
            },
        ],
    }

    in_stock_items: typing.Set[int] = set()

    for armory_type in _armory_data:
        for armory_item in _armory_data[armory_type]:
            quantity = armory_item.get("available") or armory_item.get("quantity") or 0
            minimum = faction_config["items"].get(str(armory_item["ID"]))

            in_stock_items.add(armory_item["ID"])

            if minimum is None:
                continue
            elif quantity >= minimum:
                continue

            item: typing.Optional[Item] = Item.select(Item.market_value).where(Item.tid == armory_item["ID"]).first()

            suffix = (
                ""
                if item is None or item.market_value <= 0
                else f" (worth about ${commas(item.market_value * (minimum - quantity))})"
            )
            payload["embeds"].append(
                {
                    "title": "Low Armory Stock",
                    "description": f"{faction.name} is currently low on {armory_item['name']} ({commas(quantity)} "
                    f"remaining). {commas(minimum - quantity)}x must be bought to meet the minimum quantity{suffix}.",
                    "color": SKYNET_ERROR,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "footer": {"text": torn_timestamp()},
                }
            )

            if len(payload["embeds"]) == 10:
                discordpost.delay(
                    f"channels/{faction_config['channel']}/messages",
                    payload=payload,
                    channel=faction_config["channel"],
                ).forget()
                payload["embeds"].clear()

    out_of_stock_item: int
    for out_of_stock_item in set(map(int, faction_config["items"])) - in_stock_items:
        minimum = faction_config["items"].get(str(out_of_stock_item))
        item: typing.Optional[Item] = (
            Item.select(Item.market_value, Item.name).where(Item.tid == out_of_stock_item).first()
        )

        if minimum is None:
            continue

        suffix = (
            ""
            if item is None or item.market_value <= 0
            else f" (worth about ${commas(item.market_value * (minimum - quantity))})"
        )

        payload["embeds"].append(
            {
                "title": "Armory Out of Stock",
                "description": f"{faction.name} is currently out of stock of {item.name}. "
                f"{commas(minimum)}x must be bought to meet the minimum quantity{suffix}.",
                "color": SKYNET_ERROR,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "footer": {"text": torn_timestamp()},
            }
        )

        if len(payload["embeds"]) == 10:
            discordpost.delay(
                f"channels/{faction_config['channel']}/messages",
                payload=payload,
                channel=faction_config["channel"],
            ).forget()
            payload["embeds"].clear()

    if len(payload["embeds"]) != 0:
        discordpost.delay(
            f"channels/{faction_config['channel']}/messages",
            payload=payload,
            channel=faction_config["channel"],
        ).forget()
