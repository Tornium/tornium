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

defmodule Tornium.Schema.Chain do
  @moduledoc """
  A chain for a faction.

  If the chain is not in cooldown yet, the chain `:end_timestamp` will be `nil` and the
  `:length` will be updated as the chain progresses.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          chain_id: pos_integer(),
          faction_id: pos_integer(),
          faction: Tornium.Schema.Faction.t(),
          length: 0..100_000,
          start_timestamp: DateTime.t(),
          end_timestamp: DateTime.t() | nil
        }

  @primary_key {:chain_id, :integer, autogenerate: false}
  schema "chain" do
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    field(:length, :integer)
    field(:start_timestamp, :utc_datetime)
    field(:end_timestamp, :utc_datetime)
  end
end
