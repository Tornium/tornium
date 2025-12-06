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
  alias Torngen.Client.Schema.UserCompetitionElimination

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

  This updates the user against a server's admins.
  """
  @spec update_member(user_id :: pos_integer(), server_id :: pos_integer()) ::
          {:ok, Tornium.Schema.EliminationMember.t()} | {:error, term()}
  def update_member(user_id, server_id) when is_integer(user_id) and is_integer(server_id) do
    # TODO: add typespec for error
    %DateTime{year: year} = DateTime.utc_now()

    member =
      Tornium.Schema.EliminationMember
      |> where([m], m.user_id == ^user_id)
      |> join(:inner, [m], t in assoc(m, :team), on: m.team_id == t.guid)
      |> where([m, t], m.year == ^year)
      |> first()
      |> Repo.one()

    server =
      Tornium.Schema.Server
      |> where([s], s.sid == ^server_id)
      |> first()
      |> Repo.one()

    update_member(user_id, member, server)
  end

  @doc """
  Update a member of an Elimination team by their user ID and how the user is stored as participating in elimination this year.

  If the user has a known Elimination team, we can try to use an admin of the server that's on the same team; if there isn't an
  admin on the same team, we should just use a random admin. If there is not a known Elimination team for the user, we should
  iterate through admins' teams until we find an admin that can show the data (either they are on the same team or Torn is showing
  the data for everyone); if no data can be found, we can assume that the user isn't on an Elimintion team.
  """
  @spec update_member(
          user_id :: pos_integer(),
          member :: Tornium.Schema.EliminationMember.t() | nil,
          server :: Tornium.Schema.Server.t() | nil
        ) :: {:ok, Tornium.Schema.EliminationMember.t()} | {:error, term()}
  def update_member(
        user_id,
        %Tornium.Schema.EliminationMember{team_id: team_id} = _member,
        %Tornium.Schema.Server{admins: server_admins} = server
      )
      when is_integer(user_id) do
    case Tornium.User.Key.get_by_user(user_id) do
      %Tornium.Schema.TornKey{} = api_key ->
        # The user is in the database and has an API key. We should use their API key as it'll always have the correct data.
        update_self(api_key)

      nil ->
        # The user is in the database, so we can try to find a server admin that's also in the same team.
        %DateTime{year: year} = DateTime.utc_now()

        api_keys =
          Tornium.Schema.EliminationMember
          |> where([m], m.user_id in ^server_admins and m.team_id == ^team_id)
          |> join(:inner, [m], t in assoc(m, :team), on: m.team_id == t.guid)
          |> where([m, t], t.year == ^year)
          |> select([m, t], m.user_id)
          |> Repo.all()
          |> Enum.map(&Tornium.User.Key.get_by_user/1)
          |> Enum.reject(&is_nil/1)

        %Tornium.Schema.TornKey{api_key: api_key, user_id: api_key_owner} =
          case api_keys do
            [] ->
              # We should try to use a random admin's API key if we can't find one from an admin on the same team
              # because after the initial registration period, anyone can see anyone else's team.
              Tornium.Guild.get_random_admin_key(server)

            _ when is_list(api_keys) and api_keys != [] ->
              # Since there's an API key from a server admin that's on the same team, we should just use that in case
              # Torn changes the API response in the future.
              Enum.random(api_keys)
          end

        query =
          Tornex.SpecQuery.new(nice: -20)
          |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Id.Competition)
          |> Tornex.SpecQuery.put_parameter(:id, user_id)
          |> Tornex.SpecQuery.put_key(api_key)
          |> Tornex.SpecQuery.put_key_owner(api_key_owner)

        response = Tornex.API.get(query)

        %{UserCompetitionResponse => %{competition: %UserCompetitionElimination{} = elimination_data}} =
          Tornex.SpecQuery.parse(query, response)

        update_elimination_data(user_id, elimination_data)
    end
  end

  def update_member(user_id, member, %Tornium.Schema.Server{admins: server_admins} = _server)
      when is_integer(user_id) and is_nil(member) and is_list(server_admins) do
    # The user is not currently in the database for Elimination, so we should try to use their API key since that will
    # always show the correct data. If the user is not signd into Tornium, we should try to find a random admin's key
    # that can show the team.

    case Tornium.User.Key.get_by_user(user_id) do
      %Tornium.Schema.TornKey{} = api_key ->
        update_self(api_key)

      nil ->
        # Since the user does not have an API key, we should try various server admins until we find one that works
        %DateTime{year: year} = DateTime.utc_now()

        Tornium.Schema.EliminationMember
        |> where([m], m.user_id in ^server_admins)
        |> join(:inner, [m], t in assoc(m, :team), on: m.team_id == t.guid)
        |> where([m, t], m.year == ^year)
        |> select([m, t], {m.user_id, t.name})
        |> Repo.all()
        |> Enum.map(fn {user_id, team_name} -> {user_id, team_name, Tornium.User.Key.get_by_user(user_id)} end)
        |> Enum.reject(fn {_user_id, _team_name, api_key} -> is_nil(api_key) end)
        |> Enum.group_by(fn {_user_id, team_name, _api_key} -> team_name end)
        |> Map.values()
        |> Enum.find_value({:error, :no_team_found}, fn {user_id, _team_name, api_key} ->
          try do
            query =
              Tornex.SpecQuery.new(nice: -20)
              |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Competition)
              |> Tornex.SpecQuery.put_key(api_key)
              |> Tornex.SpecQuery.put_key_owner(user_id)

            response = Tornex.API.get(query)

            %{UserCompetitionResponse => %{competition: %UserCompetitionElimination{} = elimination_data}} =
              Tornex.SpecQuery.parse(query, response)

            update_elimination_data(user_id, elimination_data)
          rescue
            # We need to handle cases such as 
            _ -> false
          end
        end)
    end
  end

  @doc """
  Update a user's elimination data with their own API key by the user ID or by their API key.

  This assumes that the user has an API key, so this should be checked beforehand.
  """
  @spec update_self(pos_integer() | Tornium.Schema.TornKey.t()) ::
          {:ok, Tornium.Schema.EliminationMember.t()} | {:error, term()}
  def update_self(user_id) when is_integer(user_id) do
    case Tornium.User.Key.get_by_user(user_id) do
      %Tornium.Schema.TornKey{} = api_key ->
        update_self(api_key)

      nil ->
        {:error, :no_api_key}
    end
  end

  def update_self(%Tornium.Schema.TornKey{api_key: api_key, user_id: api_key_owner}) do
    # As the user is signed into Tornium, we can use their API key which is guaranteed to provide their elimination team
    # if that data is available and if they have joined a team.
    query =
      Tornex.SpecQuery.new(nice: -20)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Competition)
      |> Tornex.SpecQuery.put_key(api_key)
      |> Tornex.SpecQuery.put_key_owner(api_key_owner)

    response = Tornex.API.get(query)

    %{UserCompetitionResponse => %{competition: %UserCompetitionElimination{} = elimination_data}} =
      Tornex.SpecQuery.parse(query, response)

    update_elimination_data(api_key_owner, elimination_data)
  end

  @spec update_elimination_data(
          user_id :: pos_integer(),
          elimination_data :: UserCompetitionElimination.t()
        ) :: {:ok, Tornium.Schema.EliminationMember.t()} | {:error, term()}
  defp update_elimination_data(user_id, %UserCompetitionElimination{
         team: team_name,
         score: member_score,
         attacks: member_attacks
       })
       when is_integer(user_id) do
    %DateTime{year: year} = DateTime.utc_now()

    %Tornium.Schema.EliminationTeam{guid: team_id} =
      Tornium.Schema.EliminationTeam
      |> where([t], t.year == ^year and t.name == ^team_name)
      |> first()
      |> Repo.one()

    %Tornium.Schema.EliminationMember{guid: member_guid} =
      member =
      %Tornium.Schema.EliminationMember{
        guid: Ecto.UUID.generate(),
        user_id: user_id,
        team_id: team_id
      }
      |> Repo.insert(on_conflict: :nothing, conflict_target: [:user_id, :team_id], returning: true)

    %Tornium.Schema.EliminationRecord{
      guid: Ecto.UUID.generate(),
      member_id: member_guid,
      timestamp: DateTime.utc_now(),
      score: member_score,
      attacks: member_attacks
    }
    |> Repo.insert()

    {:ok, member}
  end
end
