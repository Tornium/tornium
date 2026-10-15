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


@db.atomic()
def ingest_crime_data(
    oc_type: OrganizedCrimeType,
    oc_id: int,
    scenes: typing.List[dict],
    crime_slot_assignments: typing.List[tuple],
    user_id: int,
) -> None:
    path = parse_scenario_path(scenes, crime_slot_assignments)
    seen_data = {
        "last_seen_at": datetime.datetime.utcnow(),
        "last_seen_by": user_id,
        "last_seen_in": oc_id,
    }

    scene: dict
    for scene in scenes:
        # We want to look for scenes that are decision nodes resulting in a success or a failure.
        # From that scene, the previous scene with a similar name should be decision node with
        # success/failure node being the text describing it (eg A2-C1F -> A2-C1).
        if scene["type"] not in ("success", "failed"):
            print("skipping invalid type:", scene)
            continue
        elif scene["slug"][-1] not in ("P", "F"):
            print("skipping slug suffix:", scene)
            continue

        print("ingesting ", scene)

        base_slug = scene["slug"][:-1]
        decision_node = next(filter(lambda scene: scene["slug"] == base_slug, scenes), None)

        if decision_node is None:
            # Since there's no decision node found, we should exit early as this would cause a break
            # in the graph.
            print(f"No decision node found for {scene['slug']}")
            return
        elif decision_node["type"] != "event":
            print(f"Invalid decision node type {decision_node['type']}")
            return

        now = datetime.datetime.utcnow()
        node = (
            OrganizedCrimeGraphNode.insert(
                guid=uuid.uuid4(),
                oc_type_id=oc_type.guid,
                scene_id=decision_node["ID"],
                scene_slug=decision_node["slug"],
                last_seen_at=now,
                last_seen_by=user_id,
                last_seen_in=oc_id,
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
            .returning(OrganizedCrimeGraphNode)
            .execute()[0]
        )
        OrganizedCrimeGraphNodeVariant.insert(
            guid=uuid.uuid4(),
            node_id=node.guid,
            text=normalize_scene_text(scene["dialogues"][0]["description"], crime_slot_assignments),
            effective_weight=1.0,
            last_seen_at=now,
            last_seen_by=user_id,
            last_seen_in=oc_id,
        ).on_conflict(
            conflict_target=[OrganizedCrimeGraphNodeVariant.node, OrganizedCrimeGraphNodeVariant.text],
            preserve=[
                OrganizedCrimeGraphNode.last_seen_at,
                OrganizedCrimeGraphNode.last_seen_by,
                OrganizedCrimeGraphNode.last_seen_in,
            ],
        ).execute()

        if previous_node is not None:
            OrganizedCrimeGraphEdge.insert(
                guid=uuid.uuid4(),
                success=decision_node["type"] == "success",
                from_node=previous_node.guid,
                to_node=node.guid,
                effective_weight=1.0,
                last_seen_at=now,
                last_seen_by=user_id,
                last_seen_in=oc_id,
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
            ).execute()

        # TODO: We need to increment the weight of the edge and node variant if they already
        # exist when we're upserting them.
        # TODO: We need to exponential decay the weights of the other edges and other node
        # variants at the end of thsi

        previous_node = node

        # TODO: We also need to handle terminal nodes somehow

    OrganizedCrime.update(scenario_ingested_at=datetime.datetime.utcnow()).where(
        OrganizedCrime.oc_id == oc_id
    ).execute()


@dataclasses.dataclass(frozen=True)
class ScenarioPathNode:
    scene_id: int
    slug: str
    text: typing.Optional[str]
    success: bool
    terminal: bool = False


SCENARIO_OUTCOME_SLUG_REGEX = re.compile(r"^(?P<base>.+)(?P<outcome>[PF])$")
SCENARIO_OUTCOME_TYPES = {"P": "success", "F": "failed"}


def parse_scenario_path(
    scenes: typing.List[dict], crime_slot_assignments: typing.List[tuple]
) -> typing.List[ScenarioPathNode]:
    # We want to parse the list of scenes provided by Torn into the linear path:
    #   root -> decision nodes -> terminal node
    if len(scenes) == 0:
        raise ValueError("No scenes were provided")

    mapped_scenes = {scene["slug"]: scene for scene in scenes}
    path = [ScenarioPathNode(scene_id=0, slug="__root__", text=None, success=True)]

    for scene in scenes:
        # We want to look for scenes that are decision nodes resulting in a success or a failure.
        # From that scene, the previous scene with a similar name should be decision node with
        # success/failure node being the text describing it (eg A2-C1F -> A2-C1).
        if scene["type"] not in SCENARIO_OUTCOME_TYPES.values():
            print("skipping invalid type:", scene)
            continue

        slug_match = SCENARIO_OUTCOME_SLUG_REGEX.match(scene["slug"])
        if slug_match is None:
            continue
        elif scene["type"] != SCENARIO_OUTCOME_TYPES[slug_match["outcome"]]:
            raise ValueError(f"Scenario outcome scene {scene['slug']} has mismatched type {scene['type']}")

        decision_node = mapped_scenes.get(slug_match["base"])
        if decision_node is None:
            raise ValueError(f"Unable to find matching slug base for scene {scene['slug']}")
        elif decision_node["type"] not in ("event", "objective"):
            raise ValueError(f"Invalid decision node type {scene['type']}")

        path.append(
            ScenarioPathNode(
                scene_id=decision_node["ID"],
                slug=decision_node["slug"],
                text=normalize_scene_text(scene["dialogues"][0]["description"], crime_slot_assignments),
                success=slug_match["outcome"] == "P",
            )
        )

    if len(path) <= 1:
        raise ValueError("Scenario doesn't have enough decision nodes")

    terminal_node = scenes[-1]
    path.append(
        ScenarioPathNode(
            scene_id=terminal_node["ID"],
            slug=terminal_node["slug"],
            text=normalize_scene_text(decision_node["dialogues"][0]["description"], crime_slot_assignments),
            success=True,
            terminal=True,
        )
    )

    return path


def normalize_scene_text(scene_text: str, crime_slot_assignments: typing.List[tuple]) -> str:
    # We want to replace the member-specific IDs in the scene text with strings representing
    # the position so that the scene text from different OCs/factions doesn't get split into
    # seperate node variants.
    # For this, we can use the same format the tornium_oc_graph library uses:
    #   `<{crime_position_name.lower()}_{crime_position_index}>`
    # such that Cat Burglar #1 would become
    #   `<cat_burglar_1>`

    USER_ID_REGEX = re.compile(r"userId-(\d+)")
    placeholders = {
        member_id: f"<{'_'.join(position_name.lower().split(' '))}_{position_index}>"
        for position_name, position_index, member_id in crime_slot_assignments
    }

    def replace_user_id(match: re.Match) -> str:
        member_id = int(match.group(1))

        if member_id not in placeholders:
            raise ValueError(f"Unknown member ID {member_id} referenced in scene text.")

        return placeholders[member_id]

    return " ".join(USER_ID_REGEX.sub(replace_user_id, scene_text).split())
