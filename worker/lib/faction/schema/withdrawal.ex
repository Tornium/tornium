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

defmodule Tornium.Schema.Withdrawal do
  @moduledoc """
  Schema for faction banking requests.
  """
  use Ecto.Schema

  @type withdrawal_status() :: :unfulfilled | :fulfilled | :cancelled | :timed_out
  @type t :: %__MODULE__{
          wid: pos_integer(),
          guid: Ecto.UUID.t(),
          faction_id: pos_integer(),
          faction: Tornium.Schema.Faction.t(),
          amount: pos_integer(),
          cash_request: boolean(),
          requester_id: pos_integer(),
          requester: Tornium.Schema.User.t(),
          time_requested: DateTime.t(),
          expires_at: DateTime.t() | nil,
          status: withdrawal_status(),
          fulfiller: pos_integer() | -1 | nil,
          time_fulfilled: DateTime.t() | nil,
          withdrawal_message: pos_integer()
        }

  @primary_key {:wid, :id, autogenerate: true}
  schema "withdrawal" do
    field(:guid, Ecto.UUID)
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    field(:amount, :integer)
    field(:cash_request, :boolean)

    belongs_to(:requester, Tornium.Schema.User, references: :tid)
    field(:time_requested, :utc_datetime)
    field(:expires_at, :utc_datetime)

    field(:status, Ecto.Enum, values: [unfulfilled: 0, fulfilled: 1, cancelled: 2, timed_out: 3])

    field(:fulfiller, :integer)
    field(:time_fulfilled, :utc_datetime)

    field(:withdrawal_message, :integer)
  end
end
