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
          leader_id: pos_integer(),
          leader: Tornium.Schema.User.t(),
          coleader_id: pos_integer() | nil,
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
  Map the faction data for a specfic faction to a `Tornium.Schema.Faction`.
  """
  @spec map(faction_data :: Torngen.Client.Schema.FactionBasic.t()) :: t()
  def map(
        %Torngen.Client.Schema.FactionBasic{
          id: id,
          name: name,
          tag: tag,
          respect: respect,
          capacity: capacity,
          leader_id: leader_id,
          co_leader_id: co_leader_id
        } = _faction_data
      ) do
    %__MODULE__{
      tid: id,
      name: name,
      tag: tag,
      respect: respect,
      capacity: capacity,
      leader_id: leader_id,
      coleader_id: co_leader_id,
      last_members: DateTime.utc_now()
    }
  end

  @doc """
  Upsert basic faction data into the database.
  """
  @spec upsert(faction_data :: Torngen.Client.Schema.FactionBasic.t()) :: t()
  def upsert(%Torngen.Client.Schema.FactionBasic{leader_id: leader_id, co_leader_id: coleader_id} = faction_data) do
    Tornium.Schema.User.ensure_exists([{leader_id, nil}, {coleader_id, nil}])

    faction_data
    |> map()
    |> Repo.insert!(
      conflict_target: :tid,
      on_conflict: {:replace, [:name, :tag, :respect, :capacity, :leader_id, :coleader_id, :last_members]},
      returning: true
    )
  end

  @spec upsert_members(
          members_data :: [Torngen.Client.Schema.FactionMember.t()],
          positions :: [Tornium.Schema.FactionPosition.t()],
          faction_id :: pos_integer()
        ) :: [Tornium.Schema.User.t()]
  def upsert_members([%Torngen.Client.Schema.FactionMember{} | _] = members_data, positions, faction_id)
      when is_list(positions) and is_integer(faction_id) do
    # Before we can insert the data, we need to map the API data into the Ecto schema struct and convert that
    # struct into a map. When converting the struct back into a map, we need to drop `:__meta__` and all keys for
    # associations (while the foreign keys for those associations should be kept) so that `Ecto.Repo.insert_all` 
    # can upsert it.
    mapped_member_data =
      members_data
      |> Enum.map(&Tornium.Schema.User.map_faction_member(&1, positions, faction_id))
      |> Enum.map(&Map.from_struct/1)
      |> Enum.map(&Map.drop(&1, [:__meta__, :faction, :faction_position, :settings]))

    {_count, upserted_members} =
      Repo.insert_all(Tornium.Schema.User, mapped_member_data,
        conflict_target: :tid,
        on_conflict:
          {:replace,
           [
             :name,
             :level,
             :faction_id,
             :faction_aa,
             :faction_position_id,
             :status,
             :last_action,
             :fedded_until,
             :last_refresh
           ]},
        returning: true
      )

    upserted_members
  end

  @doc """
  Remove the faction ID and related faction data from users who are no longer in the faction.
  """
  @spec strip_old_members(members :: [Tornium.Schema.User.t()], faction_id :: pos_integer()) :: term()
  def strip_old_members(members, faction_id) when is_list(members) and is_integer(faction_id) do
    # TODO: Test this
    current_member_ids = Enum.map(members, & &1.tid)

    Tornium.Schema.User
    |> where([u], u.tid not in ^current_member_ids and u.faction_id == ^faction_id)
    |> Repo.update_all(set: [faction_id: nil, faction_aa: false, faction_position_id: nil])
  end
end
