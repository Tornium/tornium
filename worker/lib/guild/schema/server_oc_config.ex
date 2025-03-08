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

defmodule Tornium.Schema.ServerOCConfig do
  use Ecto.Schema

  @type t :: %__MODULE__{
          server: Tornium.Schema.Server.t(),
          faction: Tornium.Schema.Faction.t(),
          enabled: boolean(),
          tool_channel: integer(),
          tool_roles: [integer()],
          tool_crimes: [String.t()],
          delayed_channel: integer(),
          delayed_roles: [integer()],
          delayed_crimes: [String.t()]
        }

  @primary_key false
  schema "server_oc_config" do
    belongs_to(:server, Tornium.Schema.Server, references: :sid)
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    field(:enabled, :boolean)

    field(:tool_channel, :integer)
    field(:tool_roles, {:array, :integer})
    field(:tool_crimes, {:array, :string})

    field(:delayed_channel, :integer)
    field(:delayed_roles, {:array, :integer})
    field(:delayed_crimes, {:array, :string})
  end
end
