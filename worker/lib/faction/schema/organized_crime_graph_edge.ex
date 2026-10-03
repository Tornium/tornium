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

defmodule Tornium.Schema.OrganizedCrimeGraphEdge do
  @moduledoc """
  An edge of the graph for an OC scenario.

  The edge represents the transition between two decision nodes for either a successful
  or a failure (by `:success`) of the `:from_node` decision node to the next node `:to_node`.

  The edge has an `:effective_weight` representing the frequency that edge is seen in
  user-provided data. When seen in provided data, the `:effective_weight` is incremented.
  When data is ingested for that OC type but that edge is not included in the data, the
  `:effective_weight` of the edge is exponentially decayed.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          success: boolean(),
          from_node_id: Ecto.UUID.t(),
          from_node: Tornium.Schema.OrganizedCrimeGraphNode.t(),
          to_node_id: Ecto.UUID.t(),
          to_node: Tornium.Schema.OrganizedCrimeGraphNode.t(),
          effective_weight: float(),
          last_seen_at: DateTime.t(),
          last_seen_by_id: pos_integer(),
          last_seen_by: Tornium.Schema.User.t(),
          last_seen_in_id: pos_integer(),
          last_seen_in: Tornium.Schema.OrganizedCrime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_graph_edge" do
    field(:success, :boolean)
    belongs_to(:from_node, Tornium.Schema.OrganizedCrimeGraphNode, references: :guid)
    belongs_to(:to_node, Tornium.Schema.OrganizedCrimeGraphNode, references: :guid)

    field(:effective_weight, :float)

    field(:last_seen_at, :utc_datetime)
    belongs_to(:last_seen_by, Tornium.Schema.User, references: :tid)
    belongs_to(:last_seen_in, Tornium.Schema.OrganizedCrime, references: :oc_id)
  end
end
