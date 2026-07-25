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
  import Ecto.Query
  alias Tornium.Repo

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
          chain_alert_roles: [Tornium.Discord.role()],
          chain_alert_minimum: 0..300
        }

  @primary_key false
  schema "serverattackconfig" do
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
    field(:chain_alert_minimum, :integer)
  end

  @doc """
  Get the attack notification configuration for the faction in its linked server.
  """
  @spec config(faction_id :: pos_integer()) :: t() | nil
  def config(faction_id) when is_integer(faction_id) do
    Tornium.Schema.ServerAttackConfig
    |> where([c], c.faction_id == ^faction_id)
    |> join(:inner, [c], f in assoc(c, :faction), on: c.faction_id == f.tid)
    |> join(:inner, [c, f], s in assoc(f, :guild), on: f.guild_id == s.sid)
    |> where([c, f, s], ^faction_id in s.factions)
    |> first()
    |> Repo.one()
  end
end
