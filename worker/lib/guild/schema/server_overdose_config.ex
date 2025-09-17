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

  If `:channel` is `nil`, OD notifications are disabled for that server and faction.

  ## Fields
    * `:guid` - UUID primary key
    * `:server_id` - Foreign key to the associated server (`Tornium.Schema.Server`).
    * `:faction_id` - Foreign key to the associated faction (`Tornium.Schema.Faction`).
    * `:channel` - Optional channel ID where overdose notifications are sent.
  """

  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          server_id: integer(),
          server: Tornium.Schema.Server.t(),
          faction_id: integer(),
          faction: Tornium.Schema.Faction.t(),
          channel: integer() | nil
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "server_overdose_config" do
    belongs_to(:server, Tornium.Schema.Server, references: :sid)
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    field(:channel, :integer)
  end

  @doc """
  Gets the overdose configuration for a faction and server.

  The faction and server are assumed to be linked. This needs to be checked separately or `get_by_faction/1`
  should be used.
  """
  @spec get(faction_id :: integer(), guild_id :: integer()) :: t() | nil
  def get(faction_id, guild_id) when is_integer(faction_id) and is_integer(guild_id) do
    Tornium.Schema.ServerOverdoseConfig
    |> where([c], c.server_id == ^guild_id and c.faction_id == ^faction_id)
    |> Repo.one()
  end

  @doc """
  Gets the overdose configuration for a faction's linked server.
  """
  @spec get_by_faction(tid :: integer()) :: t() | nil
  def get_by_faction(tid) when is_integer(tid) do
    faction_return =
      Tornium.Schema.Faction
      |> join(:inner, [f], s in Tornium.Schema.Server, on: f.guild_id == s.sid)
      |> where([f, s], f.tid == ^tid and f.tid in s.factions)
      |> select([f, s], [f.guild_id])
      |> Repo.one()

    case faction_return do
      [guild_id] when is_integer(guild_id) ->
        get(tid, guild_id)

      _ ->
        nil
    end
  end
end
