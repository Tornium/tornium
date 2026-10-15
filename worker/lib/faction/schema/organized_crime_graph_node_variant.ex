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

defmodule Tornium.Schema.OrganizedCrimeGraphNodeVariant do
  @moduledoc """
  Variant of the text for a node of an OC graph.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          node_id: Ecto.UUID.t(),
          node: Tornium.Schema.OrganizedCrimeGraphNode.t(),
          text: String.t(),
          effective_weight: float(),
          last_seen_at: DateTime.t(),
          last_seen_by_id: pos_integer(),
          last_seen_by: Tornium.Schema.User.t(),
          last_seen_in_id: pos_integer(),
          last_seen_in: Tornium.Schema.OrganizedCrime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_graph_node_variant" do
    belongs_to(:node, Tornium.Schema.OrganizedCrimeGraphNode, references: :guid)
    field(:text, :string)
    field(:effective_weight, :float)

    field(:last_seen_at, :utc_datetime)
    belongs_to(:last_seen_by, Tornium.Schema.User, references: :tid)
    belongs_to(:last_seen_in, Tornium.Schema.OrganizedCrime, references: :oc_id)
  end
end
