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

defmodule Tornium.Schema.OrganizedCrimeGraphNode do
  @moduledoc """
  A node of the graph of OC scene narration.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          oc_type_id: Ecto.UUID.t(),
          oc_type: Tornium.Schema.OrganizedCrimeType.t(),
          scene_id: pos_integer(),
          scene_slug: String.t(),
          last_seen_at: DateTime.t(),
          last_seen_by_id: pos_integer(),
          last_seen_by: Tornium.Schema.User.t(),
          last_seen_in_id: pos_integer(),
          last_seen_in: Tornium.Schema.OrganizedCrime.t(),
          variants: [Tornium.Schema.OrganizedCrimeGraphNodeVariant.t()]
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_graph_node" do
    belongs_to(:oc_type, Tornium.Schema.OrganizedCrimeType, references: :guid)

    field(:scene_id, :integer)
    field(:scene_slug, :string)

    field(:last_seen_at, :utc_datetime)
    belongs_to(:last_seen_by, Tornium.Schema.User, references: :tid)
    belongs_to(:last_seen_in, Tornium.Schema.OrganizedCrime, references: :oc_id)

    # TODO: add some way to calculate + store the reward of a node if there is one because it's a terminal node

    has_many(:variants, Tornium.Schema.OrganizedCrimeGraphNodeVariant, foreign_key: :node_id)
  end
end
