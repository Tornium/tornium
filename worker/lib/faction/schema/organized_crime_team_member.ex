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

defmodule Tornium.Schema.OrganizedCrimeTeamMember do
  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          user_id: integer() | nil,
          user: Tornium.Schema.User.t() | nil,
          team_id: Ecto.UUID.t(),
          team: Tornium.Schema.OrganizedCrimeTeam.t(),
          faction_id: integer(),
          faction: Tornium.Schema.Faction.t(),
          slot_type: String.t(),
          slot_count: integer(),
          slot_index: integer()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_team_member" do
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    belongs_to(:team, Tornium.Schema.OrganizedCrimeTeam, references: :guid, type: Ecto.UUID)
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    field(:slot_type, :string)
    field(:slot_count, :integer)
    field(:slot_index, :integer)
  end

  @doc """
  Find an OC team member in a specific slot.

  This will match against:
    - `:slot_type`
    - `:slot_index`

  This will also operate under the assumption the OC types match.
  """
  @spec find_slot_member(members :: [t()], slot_type :: String.t(), slot_index :: integer()) :: t() | nil
  def find_slot_member([%__MODULE__{} | _remaining_members] = members, slot_type, slot_index)
      when is_binary(slot_type) and is_integer(slot_index) do
    Enum.find(members, fn %__MODULE__{slot_type: member_slot_type, slot_index: member_slot_index} = _member ->
      member_slot_type == slot_type and member_slot_index == slot_index
    end)
  end

  @doc """
  Determine if the OC team member is a wildcard member.

  A wildcard OC team member can be filled by any member of the faction. A wildcard member is represented
  by a `nil` user and is the default value for an OC team member.

  ## Examples

    iex> Tornium.Schema.OrganizedCrimeTeamMember.wildcard?(
    ...>   %Tornium.Schema.OrganizedCrimeTeamMember{user_id: nil, user: nil}
    ...> )
    true

    iex> Tornium.Schema.OrganizedCrimeTeamMember.wildcard?(
    ...>   %Tornium.Schema.OrganizedCrimeTeamMember{user_id: 1}
    ...> )
    false
  """
  @spec wildcard?(member :: t()) :: boolean()
  def wildcard?(%__MODULE__{user_id: member_id} = _member) do
    is_nil(member_id)
  end

  @doc """
  Reset members of a faction's OC teams when the member is not in the faction.

  When a member is reset, the position of the OC team the member was in will be set to a wildcard
  member until otherwise changed.
  """
  @spec reset_outside_faction(faction_id :: non_neg_integer()) ::
          {non_neg_integer(), [Tornium.Schema.OrganizedCrimeTeamMember.t()]}
  def reset_outside_faction(faction_id) when is_integer(faction_id) do
    # TODO: Test this function
    Tornium.Schema.OrganizedCrimeTeamMember
    |> join(:inner, [m], u in assoc(m, :user), on: u.tid == m.user_id)
    |> where([m, u], m.faction_id == ^faction_id and u.faction_id != ^faction_id)
    |> select([m, u], m)
    |> update([m, u], set: [user_id: nil])
    |> Repo.update_all([])
  end
end
