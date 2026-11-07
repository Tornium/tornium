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

import collections
import dataclasses
import datetime
import re
import textwrap
import typing
import uuid

import graphviz

from .models import (
    Item,
    OrganizedCrime,
    OrganizedCrimeGraphEdge,
    OrganizedCrimeGraphNode,
    OrganizedCrimeGraphNodeVariant,
    OrganizedCrimeGraphTerminalReward,
    OrganizedCrimeType,
)


class InvalidScenarioData(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class ScenarioPathNode:
    scene_id: int
    slug: str
    text: typing.Optional[str]
    success: typing.Optional[bool]
    terminal: bool = False


class ScenarioOutcomeItem(typing.NamedTuple):
    item_name: str
    item_id: typing.Optional[int]
    quantity: int


@dataclasses.dataclass(frozen=True)
class ScenarioOutcome:
    success: bool
    cash: int
    respect: int
    items: typing.Tuple[ScenarioOutcomeItem, ...] = tuple()


SCENARIO_OUTCOME_SLUG_REGEX = re.compile(r"^(?P<base>.+)(?P<outcome>[PF])$")
SCENARIO_OUTCOME_TYPES = {"P": "success", "F": "failed"}
USER_ID_REGEX = re.compile(r"userId-(\d+)")
SCENE_PRONOUN_REGEX = re.compile(r"\b(?:he|him|himself|his)\b", re.IGNORECASE)
MASCULINE_TO_FEMININE = {"he": "she", "him": "her", "himself": "herself"}

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

# Rewards get a slower decay than edges/variants. Payouts vary from crime to crime, so a longer window
# gives a steadier average. A value seen once falls below the threshold after
# ln(0.25) / ln(0.95) ≈ 27 more crimes at that terminal, and each terminal holds at most
# 1 / (1 - λ) / threshold = 80 live rows per reward kind.
REWARD_DECAY_FACTOR = 0.95
REWARD_PRUNE_THRESHOLD = 0.25


def normalize_scene_text(scene_text: str, crime_slot_assignments: typing.List[tuple]) -> str:
    # To ensure that the same scene is mapped to the same node variant regardless of the
    # users in the OC, member IDs are replaced with position placeholders (such as
    # `{Cat Burglar:1}`) and gendered pronouns are collapsed to the feminine forms.

    placeholders = {
        member_id: f"{{{position_name}:{position_index}}}"
        for position_name, position_index, member_id in crime_slot_assignments
    }

    def replace_user_id(match: re.Match) -> str:
        member_id = int(match.group(1))
        if member_id not in placeholders:
            raise ValueError(f"Unknown member ID {member_id} referenced in scene text.")
        return placeholders[member_id]

    text = USER_ID_REGEX.sub(replace_user_id, scene_text)
    text = SCENE_PRONOUN_REGEX.sub(_normalize_pronoun, text)

    return " ".join(text.split())


def _scene_text(scene: dict, crime_slot_assignments: typing.List[tuple]) -> str:
    raw = " ".join(dialogue["description"] for dialogue in scene["dialogues"])
    return normalize_scene_text(raw, crime_slot_assignments)


def _normalize_pronoun(match: re.Match) -> str:
    # We want to normalize pronouns to use a single word regardless of the gender of the
    # user to avoid having two or more rows of OrganizedCrimeGraphNodeVariant for a node
    # holding the same text with different pronouns. Let us map all male pronouns into
    # the female pronoun as the male "his" and "him" both map into the female "her" which
    # is not one-to-one.

    word = match.group(0)
    lowered = word.lower()

    if lowered == "his":
        # "his bed" is a determiner (-> "her bed"); "the gun was his" is a pronoun (-> "hers")
        following = match.string[match.end() :].lstrip()
        replacement = "her" if following[:1].isalpha() else "hers"
    else:
        replacement = MASCULINE_TO_FEMININE[lowered]

    if len(word) > 1 and word.isupper():
        return replacement.upper()

    return replacement.capitalize() if word[0].isupper() else replacement


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


def parse_scenario_outcome(crime_data: dict) -> ScenarioOutcome:
    if crime_data["status"] not in ("Successful", "Failed"):
        raise InvalidScenarioData(f"Crime has not finished: {crime_data['status']}")

    faction_rewards = (crime_data.get("rewards") or {}).get("faction") or {}

    item_quantities: typing.Counter[str] = collections.Counter()
    for item in faction_rewards.get("items") or []:
        item_name = " ".join(str(item.get("name") or "").split())
        quantity = int(item.get("quantity") or 0)

        if not item_name or quantity <= 0:
            raise InvalidScenarioData(f"Invalid item reward {item!r}")

        item_quantities[item_name] += quantity

    items = []
    for name, quantity in sorted(item_quantities.items()):
        item = Item.get_by_name(name)

        if item is None:
            raise InvalidScenarioData(f"Unknown reward item {name}")

        items.append(ScenarioOutcomeItem(item_name=name, item_id=item.tid, quantity=quantity))

    return ScenarioOutcome(
        success=crime_data["status"] == "Successful",
        cash=int(faction_rewards.get("cash") or 0),
        respect=int(faction_rewards.get("respect") or 0),
        items=tuple(items),
    )


def _lock_oc_type(oc_type: OrganizedCrimeType) -> None:
    # Row lock on the OC type serializes all ingestion and pruning for this graph, which is what makes
    # the decay well-defined (and avoids deadlocks between pushes that touch rows in different orders).
    OrganizedCrimeType.select().where(OrganizedCrimeType.guid == oc_type.guid).for_update().get()


def ingest_crime_data(
    oc_type: OrganizedCrimeType,
    oc_id: int,
    scenes: typing.List[dict],
    crime_slot_assignments: typing.List[tuple],
    outcome: ScenarioOutcome,
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

        # The last element of the dipath is always its terminal node
        _observe_terminal_rewards(node_guids[-1], outcome, seen)


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


def _observe_weighted_values(values: typing.List[dict], observed: int) -> typing.List[dict]:
    updated, found = [], False

    for entry in values:
        effective_weight = entry["effective_weight"] * REWARD_DECAY_FACTOR
        if entry["value"] == observed:
            effective_weight += 1
            found = True
        if effective_weight >= REWARD_PRUNE_THRESHOLD:
            updated.append({"value": entry["value"], "effective_weight": effective_weight})

    if not found:
        updated.append({"value": observed, "effective_weight": 1.0})

    return updated


def _observe_item_quantities(
    quantities: typing.List[dict], item_quantities: typing.Dict[int, int]
) -> typing.List[dict]:
    updated, seen = [], set()

    for entry in quantities:
        effective_weight = entry["effective_weight"] * REWARD_DECAY_FACTOR
        if item_quantities.get(entry["item_id"]) == entry["quantity"]:
            effective_weight += 1
            seen.add((entry["item_id"], entry["quantity"]))
        if effective_weight >= REWARD_PRUNE_THRESHOLD:
            updated.append({**entry, "effective_weight": effective_weight})

    for item_id, quantity in item_quantities.items():
        if (item_id, quantity) not in seen:
            updated.append({"item_id": item_id, "quantity": quantity, "effective_weight": 1.0})

    return updated


def _observe_item_sets(item_sets: typing.List[dict], item_quantities: typing.Dict[int, int]) -> typing.List[dict]:
    # Every set decays on each crime at the terminal; quantities only decay when their own set is seen.
    observed_items = sorted(item_quantities)
    updated, found = [], False

    for item_set in item_sets:
        effective_weight = item_set["effective_weight"] * REWARD_DECAY_FACTOR
        quantities = item_set["quantities"]

        if item_set["items"] == observed_items:
            found = True
            effective_weight += 1
            quantities = _observe_item_quantities(quantities, item_quantities)

        if effective_weight >= REWARD_PRUNE_THRESHOLD:
            updated.append({"items": item_set["items"], "effective_weight": effective_weight, "quantities": quantities})

    if not found:
        updated.append(
            {
                "items": observed_items,
                "effective_weight": 1.0,
                "quantities": _observe_item_quantities([], item_quantities),
            }
        )

    return updated


def _observe_terminal_rewards(node_guid: uuid.UUID, outcome: ScenarioOutcome, seen: dict) -> None:
    # Safe as a read-modify-write: ingest_crime_data holds FOR UPDATE on the OC type.
    # A new row has all three rewards NULL, which satisfies the shape constraint.
    reward, _ = OrganizedCrimeGraphTerminalReward.get_or_create(node=node_guid, defaults={"guid": uuid.uuid4(), **seen})

    if not outcome.success:
        # Failure terminals keep all three rewards NULL
        if reward.respect is not None:
            raise InvalidScenarioData(f"Failed crime reached rewarding terminal {node_guid}")
    else:
        item_quantities: typing.Counter[int] = collections.Counter()
        for item in outcome.items:
            item_quantities[item.item_id] += item.quantity

        # The first successful crime decides the terminal's kind. After that, a crime with no items
        # at an item terminal is recorded as the empty set rather than switching to money.
        is_item_terminal = reward.item_sets is not None or (reward.money is None and bool(item_quantities))

        if is_item_terminal:
            if outcome.cash:
                raise InvalidScenarioData(f"Cash reward at item terminal {node_guid}")
            reward.item_sets = _observe_item_sets(reward.item_sets or [], dict(item_quantities))
        else:
            if item_quantities:
                raise InvalidScenarioData(f"Item reward at money terminal {node_guid}")
            reward.money = _observe_weighted_values(reward.money or [], outcome.cash)

        reward.respect = _observe_weighted_values(reward.respect or [], outcome.respect)

    for field, value in seen.items():
        setattr(reward, field, value)
    reward.save()


def _weighted_median(pairs: typing.List[typing.Tuple[int, float]]) -> int:
    pairs = sorted(pairs)
    half = sum(weight for _, weight in pairs) / 2
    running = 0.0
    for value, weight in pairs:
        running += weight
        if running >= half:
            return value
    return pairs[-1][0]


def _value_range_label(values: typing.List[dict], prefix: str = "") -> str:
    pairs = [(entry["value"], entry["effective_weight"]) for entry in values]
    low, high = min(value for value, _ in pairs), max(value for value, _ in pairs)
    median = f"{prefix}{_weighted_median(pairs):,}"
    return median if low == high else f"{median} ({prefix}{low:,}–{prefix}{high:,})"


def _item_set_labels(item_sets: typing.List[dict]) -> typing.List[str]:
    total_weight = sum(item_set["effective_weight"] for item_set in item_sets)
    labels = []

    for item_set in sorted(item_sets, key=lambda item_set: -item_set["effective_weight"]):
        quantities = collections.defaultdict(list)
        for entry in item_set["quantities"]:
            quantities[entry["item_id"]].append(entry["quantity"])

        parts = []
        for item_id in item_set["items"]:
            item_quantities = quantities.get(item_id) or [0]
            low, high = min(item_quantities), max(item_quantities)
            quantity = str(low) if low == high else f"{low}–{high}"
            parts.append(f"{Item.item_str(item_id)} ×{quantity}")

        labels.append(f"{' + '.join(parts) or 'no items'} ({item_set['effective_weight'] / total_weight:.0%})")

    return labels


def to_graphviz(oc_type: OrganizedCrimeType) -> graphviz.Digraph:
    nodes = {
        node.guid: node
        for node in OrganizedCrimeGraphNode.select().where(OrganizedCrimeGraphNode.oc_type == oc_type.guid)
    }
    root = next((node for node in nodes.values() if node.scene_id == ROOT_SCENE_ID), None)

    if root is None:
        raise ValueError(f"No scenario graph has been ingested for {oc_type.name}")

    variants = collections.defaultdict(list)
    for variant in (
        OrganizedCrimeGraphNodeVariant.select(OrganizedCrimeGraphNodeVariant)
        .join(OrganizedCrimeGraphNode)
        .where(OrganizedCrimeGraphNode.oc_type == oc_type.guid)
        .order_by(
            OrganizedCrimeGraphNodeVariant.effective_weight.desc(), OrganizedCrimeGraphNodeVariant.last_seen_at.desc()
        )
    ):
        variants[variant.node_id].append(variant)

    edges = collections.defaultdict(list)
    for edge in (
        OrganizedCrimeGraphEdge.select(OrganizedCrimeGraphEdge)
        .join(OrganizedCrimeGraphNode, on=(OrganizedCrimeGraphEdge.from_node == OrganizedCrimeGraphNode.guid))
        .where(OrganizedCrimeGraphNode.oc_type == oc_type.guid)
        .order_by(OrganizedCrimeGraphEdge.effective_weight.desc(), OrganizedCrimeGraphEdge.last_seen_at.desc())
    ):
        if edge.to_node_id in nodes:
            edges[(edge.from_node_id, edge.success)].append(edge)

    rewards = {
        reward.node_id: reward
        for reward in OrganizedCrimeGraphTerminalReward.select().where(
            OrganizedCrimeGraphTerminalReward.node.in_(list(nodes))
        )
    }

    has_outgoing = {from_guid for from_guid, _ in edges}
    dot = graphviz.Digraph(
        name=oc_type.name,
        node_attr={"shape": "box", "fontsize": "10"},
    )

    for guid in nodes:
        node = nodes[guid]
        if guid == root.guid:
            dot.node(str(guid), "Start", shape="circle")
            continue

        node_variants = variants.get(guid, [])
        lines = [node.scene_slug, *textwrap.wrap(node_variants[0].text if node_variants else "", 40)]
        if len(node_variants) > 1:
            lines.append(f"(+{len(node_variants) - 1} other variants)")

        reward = rewards.get(guid)
        if reward is not None and reward.respect is None:
            lines.append("Failure")
        elif reward is not None and reward.respect is not None:
            lines.append(f"respect {_value_range_label(reward.respect)}")

            if reward.money is not None:
                lines.append(f"money {_value_range_label(reward.money, '$')}")
            if reward.item_sets is not None:
                lines.extend(_item_set_labels(reward.item_sets))

        dot.node(
            str(guid),
            graphviz.nohtml("\\n".join(lines)),
            shape="box" if guid in has_outgoing else "doubleoctagon",
        )

    for (from_guid, success), candidates in edges.items():
        if from_guid not in nodes:
            continue

        for rank, edge in enumerate(candidates):
            if edge.to_node_id not in nodes:
                continue

            outcome = "" if from_guid == root.guid else ("pass " if success else "fail ")
            dot.edge(
                str(from_guid),
                str(edge.to_node_id),
                label=f"{outcome}({edge.effective_weight:.2f})",
                color="darkgreen" if success else "firebrick",
                style="solid" if rank == 0 else "dashed",
            )

    return dot
