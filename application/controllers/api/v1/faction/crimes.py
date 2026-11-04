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

import dataclasses
import datetime
import itertools
import json
import re
import typing
import uuid

from flask import jsonify, request
from peewee import DoesNotExist
from tornium_commons.db_connection import db
from tornium_commons.models import (
    Faction,
    OrganizedCrime,
    OrganizedCrimeCPR,
    OrganizedCrimeGraphEdge,
    OrganizedCrimeGraphNode,
    OrganizedCrimeGraphNodeVariant,
    OrganizedCrimeSlot,
    OrganizedCrimeSlotType,
    OrganizedCrimeType,
    ServerOCConfig,
    ServerOCRangeConfig,
    User,
)

from controllers.api.v1.decorators import (
    global_cache,
    ratelimit,
    require_oauth,
    session_required,
)
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@require_oauth()
@ratelimit
@global_cache
def get_oc_names(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    oc_names: typing.List[str] = [oc_type.name for oc_type in OrganizedCrimeType.select(OrganizedCrimeType.name)]

    return jsonify(oc_names), 200, api_ratelimit_response(key)


@require_oauth()
@ratelimit
@global_cache
def get_oc_slots(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    slots = OrganizedCrimeSlotType.select(
        OrganizedCrimeSlotType.guid, OrganizedCrimeType.name, OrganizedCrimeSlotType.name, OrganizedCrimeSlotType.number
    ).join(OrganizedCrimeType)

    return (
        jsonify(
            [
                {
                    "guid": slot_type.guid,
                    "oc": slot_type.oc_type.name,
                    "position_name": slot_type.name,
                    "position_index": slot_type.number,
                }
                for slot_type in slots
            ]
        ),
        200,
        api_ratelimit_response(key),
    )


@require_oauth("faction:crimes", "faction")
@ratelimit
def get_delays(faction_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    before = request.args.get("before")
    after = request.args.get("after")

    if isinstance(before, str) and not before.isdigit():
        return make_exception_response("0000", key)
    elif isinstance(after, str) and not after.isdigit():
        return make_exception_response("0000", key)

    try:
        if before is not None:
            before = int(before)
        if after is not None:
            after = int(after)

        limit = min(int(request.args.get("limit", 100)), 100)
    except (ValueError, TypeError):
        return make_exception_response("0000", key)

    if before is not None and after is not None and before >= after:
        return make_exception_response("0000", key)

    slots = (
        OrganizedCrimeSlot.select()
        .join(User)
        .where((OrganizedCrimeSlot.delayer == True) & (User.faction_id == faction_id))
        .order_by(OrganizedCrimeSlot.oc_id.desc())
        .limit(limit)
    )

    if before is not None:
        slots = slots.where(OrganizedCrimeSlot.oc_id <= before)
    if after is not None:
        slots = slots.where(OrganizedCrimeSlot.oc_id >= after)

    return [
        {
            "oc_id": slot.oc_id,
            "user_id": slot.user_id,
            "oc_position": slot.crime_position,
            "oc_position_index": slot.crime_position_index,
            "delay_reason": slot.delayed_reason,
        }
        for slot in slots
    ]


@session_required
@ratelimit
def get_members_cpr_slot(faction_id: int, oc_name: str, oc_position_name: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if oc_name not in OrganizedCrime.oc_names():
        return make_exception_response("1105", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not kwargs["user"].can_manage_crimes():
        return make_exception_response("4006", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    members = [member.tid for member in User.select(User.tid).where(User.faction_id == faction_id)]
    members_cpr: typing.Iterable[OrganizedCrimeCPR] = (
        OrganizedCrimeCPR.select()
        .join(User)
        .where(
            (User.tid.in_(members))
            & (OrganizedCrimeCPR.oc_name == oc_name)
            & (OrganizedCrimeCPR.oc_position == oc_position_name)
        )
    )

    return (
        {
            member.user_id: {
                "cpr": member.cpr,
                "name": member.user.name,
                "updated_at": int(member.updated_at.timestamp()),
            }
            for member in members_cpr
        },
        200,
        api_ratelimit_response(key),
    )


@require_oauth("faction:crimes", "faction")
@ratelimit
def get_members_cpr_oc(faction_id: int, oc_name: str, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if oc_name not in OrganizedCrime.oc_names():
        return make_exception_response("1105", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    members = [member.tid for member in User.select(User.tid).where(User.faction_id == faction_id)]
    members_cpr: typing.Iterable[OrganizedCrimeCPR] = (
        OrganizedCrimeCPR.select().join(User).where((User.tid.in_(members)) & (OrganizedCrimeCPR.oc_name == oc_name))
    )

    positions = set(member_cpr.oc_position for member_cpr in members_cpr)
    members_cpr_positions = {position: [] for position in positions}

    member_cpr: OrganizedCrimeCPR
    for member_cpr in members_cpr:
        members_cpr_positions[member_cpr.oc_position].append(member_cpr)

    for position, members_cpr_list in members_cpr_positions.items():
        members_cpr_list.sort(key=lambda member: member.cpr)

    return (
        {
            position: [
                {
                    "cpr": member.cpr,
                    "id": member.user_id,
                    "name": member.user.name,
                    "updated_at": int(member.updated_at.timestamp()),
                }
                for member in members_cpr_list
            ]
            for position, members_cpr_list in members_cpr_positions.items()
        },
        200,
        api_ratelimit_response(key),
    )


@require_oauth("faction:crimes", "faction")
@ratelimit
def get_cpr_ranges(faction_id: int, *args, **kwargs):
    user: User = kwargs["user"]
    key = f"tornium:ratelimit:{user.tid}"

    try:
        faction: Faction = Faction.select().where(Faction.tid == faction_id).get()
    except DoesNotExist:
        return make_exception_response("1102", key)

    if faction.guild is None:
        return make_exception_response("1001", key)
    elif faction_id not in faction.guild.factions:
        return make_exception_response("4021", key)

    if kwargs["method"] == "oauth" and user.faction_id != faction_id:
        # If the user is signed in through oauth, they MUST only be able to access their
        # faction's CPR range to avoid excessive data sharing.
        return make_exception_response("4022", key)
    elif kwargs["method"] == "session" and user.faction_id != faction_id and user.tid not in faction.guild.admins:
        # If the user is using the API through Tornium's website, they can access other
        # factions' CPR ranges if the user is an admin of the server linked to the
        # specified faction. Since checking if the faction has a linked server is performed
        # above, we only need to check if the user is in the linked server's list of admins.
        return make_exception_response("4020", key)

    try:
        server_oc_config: ServerOCConfig = (
            ServerOCConfig.select(
                ServerOCConfig.guid, ServerOCConfig.extra_range_global_max, ServerOCConfig.extra_range_global_min
            )
            .where((ServerOCConfig.server_id == faction.guild_id) & (ServerOCConfig.faction_id == faction_id))
            .get()
        )
    except DoesNotExist:
        return make_exception_response(
            "1000",
            key,
            details={
                "element": "server_oc_config",
                "message": "There is no OC config for this faction and its linked server.",
            },
        )

    ranges = (
        ServerOCRangeConfig.select()
        .where(ServerOCRangeConfig.server_oc_config_id == server_oc_config.guid)
        .order_by(ServerOCRangeConfig.oc_type_id)
    )
    grouped_ranges = itertools.groupby(ranges, lambda range_config: range_config.oc_type_id)

    local_data = {}
    for oc_type, range_configs in grouped_ranges:
        configs_list = list(range_configs)

        if not configs_list:
            continue

        # The slot names and idnexes in the local data should have the same keys as get_oc_slots
        # for continuity.
        local_data[configs_list[0].oc_type.name] = [
            {
                "guid": range_config.guid,
                "position_name": range_config.oc_slot_type.name,
                "position_index": range_config.oc_slot_type.number,
                "minimum": range_config.minimum,
                "maximum": range_config.maximum,
            }
            for range_config in configs_list
        ]

    return (
        {
            "minimum": server_oc_config.extra_range_global_min,
            "maximum": server_oc_config.extra_range_global_max,
            "local": local_data,
        },
        200,
        api_ratelimit_response(key),
    )


@require_oauth("faction:crimes", "faction")
@ratelimit
def get_optimum_slots(faction_id: int, user_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        user = User.select().where(User.tid == user_id).get()
    except DoesNotExist:
        return make_exception_response("1100", key)

    try:
        default_cpr = round(int(request.args.get("default_cpr", 75)) / 100, 3)
    except (TypeError, ValueError):
        return make_exception_response("0000", key, details={"message": "Invalid default CPR"})

    if default_cpr > 1 or default_cpr < 0:
        return make_exception_response("0000", key, details={"message": "The default CPR must be between 0 and 100"})
    elif user.faction_id != faction_id:
        return make_exception_response("4022", key)
    elif kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    current_slot: typing.Optional[OrganizedCrimeSlot] = (
        OrganizedCrimeSlot.select(OrganizedCrime.oc_id, OrganizedCrime.oc_name)
        .join(OrganizedCrime)
        .where((OrganizedCrimeSlot.user_id == user_id) & (OrganizedCrime.executed_at.is_null(True)))
        .order_by(OrganizedCrimeSlot.user_joined_at.desc())
        .first()
    )
    current_ev = None

    if current_slot is not None:
        current_oc_slots: typing.List[OrganizedCrimeSlot] = list(
            OrganizedCrimeSlot.select().where(OrganizedCrimeSlot.oc_id == current_slot.oc_id)
        )

        try:
            current_ev = OrganizedCrime.expected_value(current_slot.oc.oc_name, current_oc_slots, default=1.0)
        except KeyError as e:
            return make_exception_response("0000", key, details={"message": str(e)})

    all_slots: typing.List[OrganizedCrimeSlot] = list(
        OrganizedCrimeSlot.select(
            OrganizedCrimeSlot.user_id,
            OrganizedCrimeSlot.crime_position,
            OrganizedCrimeSlot.crime_position_index,
            OrganizedCrimeSlot.user_success_chance,
            OrganizedCrime.oc_id,
            OrganizedCrime.oc_name,
        )
        .join(OrganizedCrime)
        .where(
            (OrganizedCrime.faction_id == faction_id)
            & (OrganizedCrime.executed_at.is_null(True))
            & (OrganizedCrime.status.in_(["planning", "recruiting"]))
        )
    )

    oc_slots = {}

    slot: OrganizedCrimeSlot
    for slot in all_slots:
        oc_slots.setdefault(slot.oc_id, []).append(slot)

    user_cprs = {
        (cpr.oc_name, cpr.oc_position): cpr.cpr
        for cpr in OrganizedCrimeCPR.select(
            OrganizedCrimeCPR.oc_name, OrganizedCrimeCPR.oc_position, OrganizedCrimeCPR.cpr
        ).where(OrganizedCrimeCPR.user_id == user_id)
    }
    possible_slots = []

    for oc_id, slots in oc_slots.items():
        oc_name = slots[0].oc.oc_name
        try:
            current_oc_ev = round(OrganizedCrime.expected_value(oc_name, slots, default=0.7))
            current_oc_probability = round(OrganizedCrime.probability(oc_name, slots, default=0.7), 3)
        except (KeyError, RuntimeError):
            continue

        slot: OrganizedCrimeSlot
        for slot in slots:
            try:
                slot_cpr = user_cprs[(oc_name, slot.crime_position)]
            except KeyError:
                possible_slots.append(
                    {
                        "oc_id": oc_id,
                        "oc_position": slot.crime_position,
                        "oc_position_index": slot.crime_position_index,
                        "crime_success_probability": None,
                        "expected_value": None,
                        "probability": None,
                        "team_expected_value_change": None,
                        "team_probability_change": None,
                        "user_expected_value_change": None,
                    }
                )
                continue

            modified_slots = []

            # We want a list of slots corresponding to this OC ID where the current `slot` is replaced with a slot the user would be in
            set_slot: OrganizedCrimeSlot
            for set_slot in slots:
                if (
                    set_slot.crime_position == slot.crime_position
                    and set_slot.crime_position_index == slot.crime_position_index
                ):
                    modified_slots.append(
                        OrganizedCrimeSlot(
                            crime_position=set_slot.crime_position,
                            crime_position_index=set_slot.crime_position_index,
                            user_success_chance=slot_cpr,
                            user_id=user_id,
                        )
                    )
                    continue

                modified_slots.append(set_slot)

            try:
                expected_value = round(OrganizedCrime.expected_value(oc_name, modified_slots, default=0.7))
                probability = round(OrganizedCrime.probability(oc_name, modified_slots, default=0.7), 3)
            except KeyError:
                possible_slots.append(
                    {
                        "oc_id": oc_id,
                        "oc_position": slot.crime_position,
                        "oc_position_index": slot.crime_position_index,
                        "crime_success_probability": slot_cpr,
                        "expected_value": None,
                        "probability": None,
                        "team_expected_value_change": None,
                        "team_probability_change": None,
                        "user_expected_value_change": None,
                    }
                )
                continue

            possible_slots.append(
                {
                    "oc_id": oc_id,
                    "oc_position": slot.crime_position,
                    "oc_position_index": slot.crime_position_index,
                    "crime_success_probability": slot_cpr,
                    "expected_value": expected_value,
                    "probability": probability,
                    "team_expected_value_change": (
                        None if current_oc_ev == 0 else round((expected_value - current_oc_ev) / current_oc_ev, 4)
                    ),
                    "team_probability_change": (
                        None
                        if current_oc_probability == 0
                        else round((probability - current_oc_probability) / current_oc_probability, 4)
                    ),
                    "user_expected_value_change": (
                        None if current_ev == 0 else round((expected_value - current_ev) / current_ev, 4)
                    ),
                }
            )

    return possible_slots, 200, api_ratelimit_response(key)


@require_oauth()
@ratelimit
def upload_crime_scenarios(faction_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    data = json.loads(request.get_data().decode("utf-8"))

    if kwargs["user"].faction_id != faction_id:
        return make_exception_response("4022", key)
    elif not Faction.select().where(Faction.tid == faction_id).exists():
        return make_exception_response("1102", key)

    if not isinstance(data["success"], bool) or not data["success"]:
        # The data provided by Torn is not something the user can control, so let us just
        # do an early, quiet exit.
        return make_exception_response("0000", key, details={"message": "Invalid Torn data"})

    crimes = data.get("data") or []
    provided_oc_ids = [crime_data["ID"] for crime_data in crimes]
    crimes_found = {
        crime.oc_id
        for crime in OrganizedCrime.select(OrganizedCrime.oc_id).where(
            (OrganizedCrime.oc_id.in_(provided_oc_ids))
            & (OrganizedCrime.faction_id == faction_id)
            & (OrganizedCrime.scenario_ingested_at.is_null(True))
        )
    }

    for crime_data in crimes:
        oc_id: int = crime_data["ID"]

        if oc_id not in crimes_found:
            # This OC isn't the database, so we are unable to verify the data provided.
            continue
        elif crime_data["status"] not in ("Failed", "Successful"):
            # Presumably this OC is still in planning, so we should skip it.
            continue

        oc_type: typing.Optional[OrganizedCrimeType] = OrganizedCrimeType.get_by_name(crime_data["scenario"]["name"])
        if oc_type is None:
            continue

        crime_slots_base_query = OrganizedCrimeSlot.select().where(OrganizedCrimeSlot.oc_id == oc_id)
        crime_slots_is_valid = True
        crime_slot_assignments = []

        crime_slot: dict
        for crime_slot in crime_data["playerSlots"]:
            # The slot index is zero-indexed in Tornium but one-indexed by Torn, so we
            # need to remove one to ensure the DB query is correct.
            slot_member_id = int(crime_slot["player"]["ID"])
            slot_index = int(crime_slot["key"][1]) - 1
            slot_position_name, slot_position_index = OrganizedCrimeSlotType.parse_slot(crime_slot["name"])
            crime_slot_assignments.append((slot_position_name, slot_position_index, slot_member_id))

            print(slot_member_id, slot_index, slot_position_name, slot_position_index)
            valid_member = crime_slots_base_query.where(
                (OrganizedCrimeSlot.user_id == slot_member_id)
                & (OrganizedCrimeSlot.slot_index == slot_index)
                & (OrganizedCrimeSlot.crime_position == slot_position_name)
                & (OrganizedCrimeSlot.crime_position_index == slot_position_index)
            ).exists()

            if not valid_member:
                crime_slots_is_valid = False
                break

        if not crime_slots_is_valid:
            # Some member in the provided data did not match the values in the database,
            # so we should skip it.
            continue

        ingest_crime_data(
            oc_type=oc_type,
            oc_id=oc_id,
            scenes=crime_data["scenario"]["scenes"],
            crime_slot_assignments=crime_slot_assignments,
            user_id=kwargs["user"].tid,
        )

    return make_exception_response("0001", key)


class InvalidScenarioData(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class ScenarioPathNode:
    scene_id: int
    slug: str
    text: typing.Optional[str]
    success: bool
    terminal: bool = False


SCENARIO_OUTCOME_SLUG_REGEX = re.compile(r"^(?P<base>.+)(?P<outcome>[PF])$")
SCENARIO_OUTCOME_TYPES = {"P": "success", "F": "failed"}
USER_ID_RE = re.compile(r"userId-(\d+)")

# Synthetic, text-less root shared by every crime of an OC type. It is not a scene (the prelude/objective
# is not a decision node so it isn't stored); it only exists so the edge into the first decision node
# competes and decays like any other edge.
ROOT_SCENE_ID = 0
ROOT_SCENE_SLUG = "__root__"

# Update rule for every element x in a competing group (variants of one node, or edges sharing
# (from_node, success)):   i_x <- DECAY_FACTOR * i_x + [x was verified by this push]
# An element verified on every push converges to 1 / (1 - DECAY_FACTOR) = 5.
DECAY_FACTOR = 0.8
# A freshly seen element has weight 1.0, so this must be < 1. With DECAY_FACTOR = 0.8, an element seen
# once is pruned after 7 contradicting pushes; a fully established one (~5.0) after ~14.
PRUNE_THRESHOLD = 0.25
# Elements not seen at all for this long are pruned (e.g. scenes Torn has since removed).
MAX_UNSEEN_AGE = datetime.timedelta(days=90)


def normalize_scene_text(scene_text: str, crime_slot_assignments: typing.List[tuple]) -> str:
    # Replace member-specific IDs with position placeholders so narrations from different
    # crews of the same scene compare equal, e.g. "userId-2636775 glances up" ->
    # "{Cat Burglar:1} glances up".

    placeholders = {
        member_id: f"{{{position_name}:{position_index}}}"
        for position_name, position_index, member_id in crime_slot_assignments
    }

    def replace(match: re.Match) -> str:
        member_id = int(match.group(1))
        if member_id not in placeholders:
            # Referencing someone not in the crew means the data is bogus; don't store it.
            raise InvalidScenarioData(f"Unknown member {member_id} referenced in scene text")
        return placeholders[member_id]

    return " ".join(USER_ID_RE.sub(replace, scene_text).split())


def _scene_text(scene: dict, crime_slot_assignments: typing.List[tuple]) -> str:
    raw = " ".join(dialogue["description"] for dialogue in scene["dialogues"])
    return normalize_scene_text(raw, crime_slot_assignments)


def parse_scenario_path(
    scenes: typing.List[dict], crime_slot_assignments: typing.List[tuple]
) -> typing.List[ScenarioPathNode]:
    # Turn the linear list of scenes into the path root -> decision nodes -> terminal node.

    # Raises InvalidScenarioData instead of returning partial results, so a bad push never
    # writes a broken path to the graph.

    if not scenes:
        raise InvalidScenarioData("Scenario has no scenes")

    scenes_by_slug = {scene["slug"]: scene for scene in scenes}
    path = [
        ScenarioPathNode(
            scene_id=ROOT_SCENE_ID,
            slug=ROOT_SCENE_SLUG,
            text=None,
            success=True,  # The root has exactly one outgoing transition; by convention it's a "success"
        )
    ]

    for scene in scenes:
        # Only outcome scenes (eg A2-C1P / A7-C1F) identify decision nodes. Everything else, including the
        # prelude/objective and narration-only events, is skipped unless it has an outcome scene of its own.
        # Torn uses "failed", not "failure", for the scene type.
        if scene["type"] not in SCENARIO_OUTCOME_TYPES.values():
            continue

        match = SCENARIO_OUTCOME_SLUG_REGEX.match(scene["slug"])
        if match is None:
            # Outcome-typed scene that isn't a check result, eg the terminal A9S.
            continue
        elif scene["type"] != SCENARIO_OUTCOME_TYPES[match["outcome"]]:
            raise InvalidScenarioData(f"Outcome scene {scene['slug']} has type {scene['type']}")

        decision = scenes_by_slug.get(match["base"])
        if decision is None or decision["type"] not in ("event", "objective"):
            raise InvalidScenarioData(f"No valid decision scene for {scene['slug']}")

        path.append(
            ScenarioPathNode(
                scene_id=decision["ID"],
                slug=decision["slug"],
                text=_scene_text(decision, crime_slot_assignments),
                success=match["outcome"] == "P",
            )
        )

    if len(path) == 1:
        raise InvalidScenarioData("Scenario has no decision nodes")

    # The final scene (eg A9S, or a failure ending) is the terminal node the last decision leads to.
    terminal = scenes[-1]
    path.append(
        ScenarioPathNode(
            scene_id=terminal["ID"],
            slug=terminal["slug"],
            text=_scene_text(terminal, crime_slot_assignments),
            success=None,
            terminal=True,
        )
    )
    return path


def _lock_oc_type(oc_type: OrganizedCrimeType) -> None:
    # Row lock on the OC type serializes all ingestion and pruning for this graph, which is what makes
    # the decay well-defined (and avoids deadlocks between pushes that touch rows in different orders).
    OrganizedCrimeType.select().where(OrganizedCrimeType.guid == oc_type.guid).for_update().get()


def ingest_crime_data(
    oc_type: OrganizedCrimeType,
    oc_id: int,
    scenes: typing.List[dict],
    crime_slot_assignments: typing.List[tuple],
    user_id: int,
) -> None:
    # Parse and validate everything before touching the database.
    path = parse_scenario_path(scenes, crime_slot_assignments)
    seen = {
        "last_seen_at": datetime.datetime.utcnow(),
        "last_seen_by": user_id,
        "last_seen_in": oc_id,
    }

    with OrganizedCrimeGraphNode._meta.database.atomic():
        _lock_oc_type(oc_type)

        # Each OC counts once, no matter how many faction members upload it (or how often).
        claimed = (
            OrganizedCrime.update(scenario_ingested_at=seen["last_seen_at"])
            .where((OrganizedCrime.oc_id == oc_id) & (OrganizedCrime.scenario_ingested_at.is_null()))
            .execute()
        )
        if claimed == 0:
            return

        node_guids = [_upsert_node(oc_type, node, seen) for node in path]

        for node, node_guid in zip(path, node_guids):
            if node.text is not None:
                _observe_variant(node_guid, node.text, seen)

        # The edge out of a node is labelled with *that* node's outcome, since the outcome is what
        # decides which node comes next. zip() stops before the terminal node.
        for node, from_guid, to_guid in zip(path, node_guids, node_guids[1:]):
            _observe_edge(from_guid, to_guid, node.success, seen)


def _upsert_node(oc_type: OrganizedCrimeType, node: ScenarioPathNode, seen: dict) -> uuid.UUID:
    return (
        OrganizedCrimeGraphNode.insert(
            guid=uuid.uuid4(),
            oc_type_id=oc_type.guid,
            scene_id=node.scene_id,
            scene_slug=node.slug,
            terminal=node.terminal,
            **seen,
        )
        .on_conflict(
            conflict_target=[
                OrganizedCrimeGraphNode.oc_type,
                OrganizedCrimeGraphNode.scene_id,
                OrganizedCrimeGraphNode.scene_slug,
            ],
            preserve=[
                OrganizedCrimeGraphNode.last_seen_at,
                OrganizedCrimeGraphNode.last_seen_by,
                OrganizedCrimeGraphNode.last_seen_in,
            ],
        )
        .returning(OrganizedCrimeGraphNode.guid)
        .execute()[0]
        .guid
    )


def _observe_variant(node_guid: uuid.UUID, text: str, seen: dict) -> None:
    # Verified variant: i <- λi + 1 (or 1.0 if new)
    OrganizedCrimeGraphNodeVariant.insert(
        guid=uuid.uuid4(),
        node_id=node_guid,
        text=text,
        effective_weight=1.0,
        **seen,
    ).on_conflict(
        conflict_target=[OrganizedCrimeGraphNodeVariant.node, OrganizedCrimeGraphNodeVariant.text],
        preserve=[
            OrganizedCrimeGraphNodeVariant.last_seen_at,
            OrganizedCrimeGraphNodeVariant.last_seen_by,
            OrganizedCrimeGraphNodeVariant.last_seen_in,
        ],
        update={
            OrganizedCrimeGraphNodeVariant.effective_weight: OrganizedCrimeGraphNodeVariant.effective_weight
            * DECAY_FACTOR
            + 1
        },
    ).execute()

    # Competing variants of the same node: i <- λi
    OrganizedCrimeGraphNodeVariant.update(
        effective_weight=OrganizedCrimeGraphNodeVariant.effective_weight * DECAY_FACTOR
    ).where(
        (OrganizedCrimeGraphNodeVariant.node == node_guid) & (OrganizedCrimeGraphNodeVariant.text != text)
    ).execute()


def _observe_edge(from_guid: uuid.UUID, to_guid: uuid.UUID, success: bool, seen: dict) -> None:
    # Verified edge: i <- λi + 1 (or 1.0 if new)
    OrganizedCrimeGraphEdge.insert(
        guid=uuid.uuid4(),
        from_node=from_guid,
        to_node=to_guid,
        success=success,
        effective_weight=1.0,
        **seen,
    ).on_conflict(
        conflict_target=[
            OrganizedCrimeGraphEdge.from_node,
            OrganizedCrimeGraphEdge.to_node,
            OrganizedCrimeGraphEdge.success,
        ],
        preserve=[
            OrganizedCrimeGraphEdge.last_seen_at,
            OrganizedCrimeGraphEdge.last_seen_by,
            OrganizedCrimeGraphEdge.last_seen_in,
        ],
        update={OrganizedCrimeGraphEdge.effective_weight: OrganizedCrimeGraphEdge.effective_weight * DECAY_FACTOR + 1},
    ).execute()

    # Only edges for the same (from_node, success) transition are contradicted by this push. Decaying
    # every other edge in G would steadily erode rarely-taken branches (e.g. failures) that are valid.
    OrganizedCrimeGraphEdge.update(effective_weight=OrganizedCrimeGraphEdge.effective_weight * DECAY_FACTOR).where(
        (OrganizedCrimeGraphEdge.from_node == from_guid)
        & (OrganizedCrimeGraphEdge.success == success)
        & (OrganizedCrimeGraphEdge.to_node != to_guid)
    ).execute()
