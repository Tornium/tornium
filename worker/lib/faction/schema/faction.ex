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

defmodule Tornium.Schema.Faction do
  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          tid: integer(),
          name: String.t(),
          tag: String.t(),
          respect: integer(),
          capacity: integer(),
          leader: Tornium.Schema.User.t(),
          coleader: Tornium.Schema.User.t(),
          guild: Tornium.Schema.Server.t(),
          stats_db_enabled: boolean(),
          stats_db_global: boolean(),
          od_channel: integer(),
          od_data: map(),
          last_members: DateTime.t(),
          last_attacks: DateTime.t(),
          has_migrated_oc: boolean()
        }

  @primary_key {:tid, :integer, autogenerate: false}
  schema "faction" do
    field(:name, :string)
    field(:tag, :string)
    field(:respect, :integer)
    field(:capacity, :integer)
    belongs_to(:leader, Tornium.Schema.User, references: :tid)
    belongs_to(:coleader, Tornium.Schema.User, references: :tid)

    belongs_to(:guild, Tornium.Schema.Server, references: :sid)

    field(:stats_db_enabled, :boolean)
    field(:stats_db_global, :boolean)

    field(:od_channel, :integer)
    field(:od_data, :map)

    field(:last_members, :utc_datetime_usec)
    field(:last_attacks, :utc_datetime_usec)
    field(:has_migrated_oc, :boolean)
  end

  @doc """
  Get a list of AA API keys for a specific faction.

  This will only retrieve default API keys that are not disabled or paused belonging to members of
  the specified faction ID with faction AA permissions.
  """
  @spec get_api_keys(faction_id :: pos_integer() | __MODULE__.t()) :: [Tornium.Schema.TornKey.t()]
  def get_api_keys(%__MODULE__{tid: faction_id}) do
    get_api_keys(faction_id)
  end

  def get_api_keys(faction_id) when is_integer(faction_id) do
    Tornium.Schema.TornKey
    |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
    |> where([k, u], k.default == true)
    |> where([k, u], k.disabled == false)
    |> where([k, u], k.paused == false)
    |> where([k, u], u.faction_id == ^faction_id)
    |> where([k, u], u.faction_aa == true)
    |> Repo.all()
  end
end
