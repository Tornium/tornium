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
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          server_id: integer(),
          server: Tornium.Schema.Server.t(),
          faction_id: integer(),
          faction: Tornium.Schema.Faction.t(),
          enabled: boolean(),
          tool_channel: integer() | nil,
          tool_roles: [Tornium.Discord.role()],
          tool_crimes: [String.t()],
          delayed_channel: integer() | nil,
          delayed_roles: [Tornium.Discord.role_assignable()],
          delayed_crimes: [String.t()],
          missing_member_channel: integer() | nil,
          missing_member_roles: [Tornium.Discord.role_assignable()],
          missing_member_minimum_duration: Duration.t(),
          extra_range_channel: integer() | nil,
          extra_range_roles: [Tornium.Discord.role_assignable()],
          extra_range_global_min: integer(),
          extra_range_global_max: integer(),
          extra_range_local_configs: [Tornium.Schema.ServerOCRangeConfig.t()],
          team_spawn_required_channel: integer() | nil,
          team_spawn_required_roles: [Tornium.Discord.role()],
          team_member_join_required_channel: integer() | nil,
          team_member_join_required_roles: [Tornium.Discord.role_assignable()],
          team_member_incorrect_crime_channel: integer() | nil,
          team_member_incorrect_crime_roles: [Tornium.Discord.role_assignable()],
          team_incorrect_member_channel: integer() | nil,
          team_incorrect_member_roles: [Tornium.Discord.role_assignable()],
          team_member_incorrect_slot_channel: integer() | nil,
          team_member_incorrect_slot_roles: [Tornium.Discord.role_assignable()],
          assigned_team_channel: integer() | nil,
          assigned_team_roles: [Tornium.Discord.role()]
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
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

    field(:missing_member_channel, :integer)
    field(:missing_member_roles, {:array, :integer})
    field(:missing_member_minimum_duration, :duration)

    field(:extra_range_channel, :integer)
    field(:extra_range_roles, {:array, :integer})
    field(:extra_range_global_min, :integer)
    field(:extra_range_global_max, :integer)
    has_many(:extra_range_local_configs, Tornium.Schema.ServerOCRangeConfig, foreign_key: :server_oc_config_id)

    field(:team_spawn_required_channel, :integer)
    field(:team_spawn_required_roles, {:array, :integer})

    field(:team_member_join_required_channel, :integer)
    field(:team_member_join_required_roles, {:array, :integer})

    field(:team_member_incorrect_crime_channel, :integer)
    field(:team_member_incorrect_crime_roles, {:array, :integer})

    field(:team_incorrect_member_channel, :integer)
    field(:team_incorrect_member_roles, {:array, :integer})

    field(:team_member_incorrect_slot_channel, :integer)
    field(:team_member_incorrect_slot_roles, {:array, :integer})

    field(:assigned_team_channel, :integer)
    field(:assigned_team_roles, {:array, :integer})
  end

  @doc """
  Gets the OC configuration for a faction and server.

  The faction and server are assumed to be linked. This needs to be checked separately or `get_by_faction/1`
  should be used.
  """
  @spec get(faction_id :: integer(), guild_id :: integer()) :: t() | nil
  def get(faction_id, guild_id) when is_integer(faction_id) and is_integer(guild_id) do
    Tornium.Schema.ServerOCConfig
    |> where([c], c.server_id == ^guild_id and c.faction_id == ^faction_id)
    # FIXME: This preload doesn't work
    |> preload(:extra_range_local_configs)
    |> Repo.one()
  end

  @doc """
  Gets the OC configuration for a faction's linked server.
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

  @doc """
  Returns the success chance (CPR) range as a tuple for an OC by its name.

  If there exists a local (per-OC name) range, the local range will be used. Otherwise, the global range will be used as a fallback
  """
  @spec chance_range(config :: t(), oc :: Tornium.Schema.OrganizedCrime.t()) :: {integer(), integer()}
  def chance_range(
        %__MODULE__{
          extra_range_global_min: global_min,
          extra_range_global_max: global_max,
          extra_range_local_configs: local_configs
        } = _config,
        %Tornium.Schema.OrganizedCrime{oc_name: oc_name} = _oc
      ) do
    config =
      Enum.find(local_configs, fn %Tornium.Schema.ServerOCRangeConfig{oc_name: config_oc_name} ->
        String.downcase(oc_name) == String.downcase(config_oc_name)
      end)

    case config do
      nil -> {global_min, global_max}
      %Tornium.Schema.ServerOCRangeConfig{minimum: minimum, maximum: maximum} -> {minimum, maximum}
    end
  end
end
