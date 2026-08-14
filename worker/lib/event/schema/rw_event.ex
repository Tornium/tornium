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

defmodule Tornium.Schema.RWEvent do
  @moduledoc """
  An event for a ranked war.

  Originally, the RW event will start as only being for the `:faction` at the
  `:enlistment_timestamp`. Once the faction successfully enlists, a `:ranked_war` will be set
  for the faction with a `:start_timestamp`.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          faction_id: pos_integer(),
          faction: Tornium.Schema.Faction.t(),
          enlistment_timestamp: DateTime.t(),
          start_timestamp: DateTime.t() | nil
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "rw_event" do
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    # TODO: Add a ranked war schema

    field(:enlistment_timestamp, :utc_datetime)
    field(:start_timestamp, :utc_datetime)
    # TODO: Consider adding a predicted end timestamp
  end
end
