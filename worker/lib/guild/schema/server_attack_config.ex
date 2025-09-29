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

defmodule Tornium.Schema.ServerAttackConfig do
  use Ecto.Schema

  @type t :: %__MODULE__{
          faction_id: integer(),
          faction: Tornium.Schema.Faction.t(),
          server_id: integer(),
          server: Tornium.Schema.Server.t(),
          retal_channel: integer() | nil,
          retal_roles: [Tornium.Discord.role()],
          retal_wars: boolean(),
          chain_bonus_channel: integer() | nil,
          chain_bonus_roles: [Tornium.Discord.role()],
          chain_bonus_length: non_neg_integer(),
          chain_alert_channel: integer() | nil,
          chain_alert_roles: [Tornium.Discord.role()]
        }

  @primary_key false
  schema "server_attack_config" do
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    belongs_to(:server, Tornium.Schema.Server, references: :sid)

    field(:retal_channel, :integer)
    field(:retal_roles, {:array, :integer})
    field(:retal_wars, :boolean)

    field(:chain_bonus_channel, :integer)
    field(:chain_bonus_roles, {:array, :integer})
    field(:chain_bonus_length, :integer)

    field(:chain_alert_channel, :integer)
    field(:chain_alert_roles, {:array, :integer})
  end
end
