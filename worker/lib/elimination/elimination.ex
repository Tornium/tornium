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

defmodule Tornium.Elimination do
  @moduledoc """
  Utilities related to the elimination event.
  """

  import Ecto.Query
  alias Tornium.Repo

  @doc """
  Determine if the Elimination event is active.
  """
  @spec active?() :: boolean()
  def active?() do
    # FIXME: This needs to be based upon the calendar in the future as the dates will change.
    %DateTime{month: month, day: day} = DateTime.utc_now()

    month == 12 and day < 30
  end

  @doc """
  Update all current elimination teams from API data.
  """
  @spec update_teams(team_data :: [map()]) :: [Tornium.Schema.EliminationTeam.t()]
  def update_teams(team_data) when is_list(team_data) do
    team_data
    |> Enum.map(&validate_team/1)
    |> upsert_teams()
  end

  @spec validate_team(team :: map()) :: map()
  defp validate_team(
         %{
           "position" => position,
           "teamID" => team_id,
           "name" => team_name,
           "score" => team_score,
           "lives" => team_lives,
           "participants" => _participants,
           "wins" => _wins,
           "losses" => _losses
         } = team
       )
       when is_integer(position) and is_integer(team_id) and is_binary(team_name) and is_integer(team_score) and
              is_integer(team_lives) do
    # This is just to ensure the API response hasn't changed shape.
    team
  end

  @spec upsert_teams(team_data :: [map()]) :: [Tornium.Schema.EliminationTeam.t()]
  defp upsert_teams(team_data) when is_list(team_data) do
    %DateTime{year: year} = DateTime.utc_now()

    mapped_team_data =
      Enum.map(team_data, fn %{"name" => team_name} -> %{guid: Ecto.UUID.generate(), year: year, name: team_name} end)

    {_count, teams} =
      Repo.insert_all(Tornium.Schema.EliminationTeam, mapped_team_data,
        on_conflict: :nothing,
        conflict_target: [:year, :name],
        returning: true
      )

    teams
  end

  @doc """
  Update a member of an Elimination team by user ID.
  """
  @spec update_member(member :: Tornium.Schema.EliminationMember.t(), api_key :: Tornium.Schema.TornKey.t()) ::
          {:ok, Tornium.Schema.EliminationMember.t()} | {:error, term()}
  def update_member(
        %Tornium.Schema.EliminationMember{user_id: user_id} = member,
        %Tornium.Schema.TornKey{paused: false, disabled: false} = api_key
      ) do
    # TODO: add typespec for error
  end
end
