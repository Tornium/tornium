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

defmodule Tornium.Schema.ServerOverdoseConfig do
  @moduledoc """
  Schema for overdose configuration on a per-server and per-faction basis.

  ## Fields
    * `:guid` - UUID primary key
    * `:server_id` - Foreign key to the associated server (`Tornium.Schema.Server`).
    * `:faction_id` - Foreign key to the associated faction (`Tornium.Schema.Faction`).
    * `:enabled` - Boolean flag indicating whether overdose handling/notifications are enabled for this server and faction.
    * `:channel` - Optional channel ID where overdose notifications are sent.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          server_id: integer(),
          server: Tornium.Schema.Server.t(),
          faction_id: integer(),
          faction: Tornium.Schema.Faction.t(),
          enabled: boolean(),
          channel: integer() | nil
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "server_overdose_config" do
    belongs_to(:server, Tornium.Schema.Server, references: :sid)
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    field(:enabled, :boolean)
    field(:channel, :integer)
  end
end
