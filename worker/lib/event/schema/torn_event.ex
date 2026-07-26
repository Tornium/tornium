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

defmodule Tornium.Schema.TornEvent do
  @moduledoc """
  An official in-game event or competition.
  """

  use Ecto.Schema

  @type torn_event_type() :: :competition | :event

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          title: String.t(),
          description: String.t(),
          type: torn_event_type(),
          start_timestamp: DateTime.t(),
          end_timestamp: DateTime.t(),
          configurable: boolean()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "torn_event" do
    field(:title, :string)
    field(:description, :string)
    field(:type, Ecto.Enum, values: [:competition, :event])

    field(:start_timestamp, :utc_datetime)
    field(:end_timestamp, :utc_datetime)
    field(:configurable, :boolean)
  end
end
