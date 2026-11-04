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
import textwrap

import graphviz

from .models import (
    OrganizedCrimeGraphEdge,
    OrganizedCrimeGraphNode,
    OrganizedCrimeGraphNodeVariant,
    OrganizedCrimeType,
)

# Synthetic, text-less root shared by every crime of an OC type. It is not a scene (the prelude/objective
# is not a decision node so it isn't stored); it only exists so the edge into the first decision node
# competes and decays like any other edge.
ROOT_SCENE_ID = 0
ROOT_SCENE_SLUG = "__root__"


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
