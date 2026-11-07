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

defmodule Tornium.Schema.OrganizedCrimeGraphTerminalReward do
  @moduledoc """
  Each possible reward of an OC's terminal node.
  """

  use Ecto.Schema

  @typedoc """
  The type of reward data stored for the OC graph node.
  """
  @type reward_types() :: :respect | :money | :item

  @type weighted_value() :: %{
          value: non_neg_integer(),
          effective_weight: float()
        }

  @type quantity() :: %{
          item_id: pos_integer(),
          quantity: pos_integer(),
          effective_weight: float()
        }

  @type item_set() :: %{
          items: [pos_integer()],
          effective_weight: float(),
          quantities: [quantity()]
        }

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          node_id: Ecto.UUID.t(),
          node: Tornium.Schema.OrganizedCrimeGraphNode.t(),
          money: [weighted_value()] | nil,
          respect: [weighted_value()] | nil,
          item_sets: [item_set()] | nil,
          last_seen_at: DateTime.t(),
          last_seen_by_id: pos_integer(),
          last_seen_by: Tornium.Schema.User.t(),
          last_seen_in_id: pos_integer(),
          last_seen_in: Tornium.Schema.OrganizedCrime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_graph_terminal_reward" do
    belongs_to(:node, Tornium.Schema.OrganizedCrimeGraphNode, references: :guid)

    embeds_many(:respect, Respect, primary_key: false) do
      field(:value, :integer)
      field(:effective_weight, :float)
    end

    embeds_many(:money, Money, primary_key: false) do
      field(:value, :integer)
      field(:effective_weight, :float)
    end

    embeds_many(:item_sets, ItemSet, primary_key: false) do
      field(:items, {:array, :integer})
      field(:effective_weight, :float)

      embeds_many(:quantities, Quantity, primary_key: false) do
        field(:item_id, :integer)
        field(:quantity, :integer)
        field(:effective_weight, :float)
      end
    end

    field(:last_seen_at, :utc_datetime)
    belongs_to(:last_seen_by, Tornium.Schema.User, references: :tid)
    belongs_to(:last_seen_in, Tornium.Schema.OrganizedCrime, references: :oc_id)
  end
end
