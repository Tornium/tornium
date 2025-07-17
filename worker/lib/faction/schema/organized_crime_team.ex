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

defmodule Tornium.Schema.OrganizedCrimeTeam do
  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          name: String.t(),
          oc_name: String.t(),
          faction_id: integer(),
          faction: Tornium.Schema.Faction.t(),
          members: [Tornium.Schema.OrganizedCrimeTeamMember.t()],
          crimes: [Tornium.Schema.OrganizedCrime.t()],
          current_crime: Tornium.Schema.OrganizedCrime.t(),
          required_spawn_at: DateTime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_team" do
    field(:name, :string)
    field(:oc_name, :string)
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    has_many(:members, Tornium.Schema.OrganizedCrimeTeamMember, foreign_key: :team_id)
    has_many(:crimes, Tornium.Schema.OrganizedCrime, foreign_key: :assigned_team_id)
    has_one(:current_crime, Tornium.Schema.OrganizedCrime, foreign_key: :assigned_team_id)

    field(:required_spawn_at, :utc_datetime)
  end

  @doc """
  Update the `required_spawn_at` timestamp of an `OrganizedCrimeTeam`.
  """
  @spec update_spawn_required(team :: t()) :: {non_neg_integer(), nil}
  def update_spawn_required(%__MODULE__{guid: team_guid} = _team) do
    __MODULE__
    |> update([t], set: [required_spawn_at: ^DateTime.utc_now()])
    |> where([t], t.guid == ^team_guid)
    |> Repo.update_all([])
  end

  @doc """
  Checks if the user ID exists within the OC team's member list.

  When the user ID is nil (representing a wildcard OC team member), `true` will be returned if there is
  a wildcard OC team member in the OC team.
  """
  @spec member?(team :: t(), user_id :: integer() | nil) :: boolean()
  def member?(%__MODULE__{members: members} = _team, user_id) when is_nil(user_id) do
    Enum.any?(members, fn %Tornium.Schema.OrganizedCrimeTeamMember{user_id: member_id} -> is_nil(member_id) end)
  end

  def member?(%__MODULE__{members: members} = _team, user_id) when is_integer(user_id) do
    Enum.any?(members, fn %Tornium.Schema.OrganizedCrimeTeamMember{user_id: member_id} -> member_id == user_id end)
  end
end
