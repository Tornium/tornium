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

# TODO: Store personal stats in user updates

defmodule Tornium.User do
  @moduledoc """
  Functionality related to users and updating users.
  """

  alias Tornium.Repo
  import Ecto.Query

  @minimum_update_seconds 600
  @default_update_niceness 10

  @typedoc """
  Tuple describing a user through their ID type.

  For example, `{:torn, 1}` describes the Torn user with ID 1 (Chedburn). 
  """
  @type user_id() :: {id_type :: :torn | :discord, id :: pos_integer()}

  @doc """
  Update a user by the struct.

  The user can be updated through the struct of the user or the struct of a user's API key. When
  updating the user through this function, the user must have a valid API key to use.

  ## Options
    * `:force?` - Update a user regardless of when the user was last updated (default: `false`)
    * `:niceness` - Priority of the Tornex API call (default: `10`)
  """
  @spec update(user :: Tornium.Schema.User.t() | Tornium.Schema.TornKey.t(), opts :: keyword()) ::
          {:ok, Tornium.Schema.User.t()} | {:error, Tornium.API.Error.t()}
  def update(user, opts \\ [])

  def update(%Tornium.Schema.User{tid: user_id} = _user, opts) do
    update_by_id({:torn, user_id}, nil, opts)
  end

  def update(%Tornium.Schema.TornKey{user_id: user_id} = api_key, opts) do
    update_by_id({:torn, user_id}, api_key, opts)
  end

  @doc """
  Update a user by their Torn or Discord ID.

  If the user is in the database and has an API key, we will use their API key to update their data.
  Otherwise, we'll use a random API key to update the public data for the user.

  ## Options
    * `:force?` - Update a user regardless of when the user was last updated (default: `false`)
    * `:niceness` - Priority of the Tornex API call (default: `10`)
  """
  @spec update_by_id(
          user :: user_id(),
          api_key :: Tornium.Schema.TornKey.t() | nil,
          opts :: keyword()
        ) :: {:ok, Tornium.Schema.User.t() | nil} | {:error, Tornium.API.Error.t()}
  def update_by_id(user, api_key \\ nil, opts \\ [])

  def update_by_id({:torn, id} = user, api_key, opts) when is_integer(id) and is_nil(api_key) do
    # We want to try to use the user's API key if there is one for that Torn user ID. Otherwise,
    # we can use a random user's API key.

    case Tornium.User.Key.get_by_user(id) do
      %Tornium.Schema.TornKey{user_id: ^id} = api_key ->
        update_by_id(user, api_key, opts)

      _ ->
        update_by_id(user, Tornium.User.Key.get_random!(), opts)
    end
  end

  def update_by_id({:discord, id} = user, api_key, opts) when is_integer(id) and is_nil(api_key) do
    # We want to try to use the Discord user's API key if there is a known relationship between the
    # this Discord ID and some Torn user. Otherwise, we can use a random user's API key.

    api_key =
      Tornium.Schema.User
      |> where([u], u.discord_id == ^id)
      |> join(:inner, [u], k in Tornium.Schema.TornKey, on: k.user_id == u.tid)
      |> where([u, k], k.default == true and k.disabled == false and k.paused == false)
      |> select([u, k], k)
      |> first()
      |> Repo.one()

    case api_key do
      %Tornium.Schema.TornKey{} ->
        update_by_id(user, api_key, opts)

      _ ->
        update_by_id(user, Tornium.User.Key.get_random!(), opts)
    end
  end

  def update_by_id(
        {_id_type, user_id} = user,
        %Tornium.Schema.TornKey{disabled: false, paused: false} = api_key,
        opts
      ) do
    force_update? = Keyword.get(opts, :force?, false)

    if force_update? or update_user?(user) do
      query = update_query(user_id, api_key, opts)
      response = Tornex.API.get(query)

      case response do
        %{"error" => %{"code" => 6}} ->
          # When the API returns code 6, this indicates that the ID of the user does not exist.
          {:ok, nil}

        %{"error" => %{"code" => error_code, "error" => error_message}} ->
          {:error, Tornium.API.Error.construct(error_code, error_message)}

        _ when is_map(response) ->
          query
          |> Tornex.SpecQuery.parse(response)
          |> update_data()
      end
    else
      {
        :ok,
        Tornium.Schema.User
        |> where([u], u.tid == ^user_id or u.discord_id == ^user_id)
        |> first()
        |> Repo.one()
      }
    end
  end

  @spec update_query(
          user_id :: pos_integer(),
          api_key :: Tornium.Schema.TornKey.t(),
          opts :: keyword()
        ) :: Tornex.SpecQuery.t()
  defp update_query(user_id, api_key, opts \\ [])

  defp update_query(user_id, %Tornium.Schema.TornKey{user_id: key_owner_id} = api_key, opts)
       when is_integer(user_id) and user_id == key_owner_id do
    Tornex.SpecQuery.new(niceness: Keyword.get(opts, :niceness, @default_update_niceness), resource_id: user_id)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Profile)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Discord)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Battlestats)
    |> Tornium.Schema.TornKey.put_key(api_key)
  end

  defp update_query(user_id, %Tornium.Schema.TornKey{user_id: key_owner_id} = api_key, opts)
       when is_integer(user_id) and key_owner_id != user_id do
    Tornex.SpecQuery.new(niceness: Keyword.get(opts, :niceness, @default_update_niceness), resource_id: user_id)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Id.Profile)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Id.Discord)
    |> Tornex.SpecQuery.put_parameter!(:id, user_id)
    |> Tornium.Schema.TornKey.put_key(api_key)
  end

  @doc """
  Upsert a user to the database from the parsed APIv2 response of the user's data.

  This function supports data from exactly the following sets of API calls:
    * `Torngen.Client.Path.User.Profile`, `Torngen.Client.Path.User.Discord`, and `Torngen.Client.Path.User.Battlestats`
    * `Torngen.Client.Path.User.Id.Profile` and `Torngen.Client.Path.Id.Discord`
  """
  @spec update_data(data :: map()) :: {:ok, Tornium.Schema.User.t()} | {:error, Tornium.API.Error.t()}
  def update_data(
        %{
          Torngen.Client.Path.User.Profile => %{
            UserProfileResponse =>
              %Torngen.Client.Schema.UserProfileResponse{profile: %{faction_id: faction_id}} = user_profile_data
          },
          Torngen.Client.Path.User.Discord => %{UserDiscordResponse => user_discord_data},
          Torngen.Client.Path.User.Battlestats => %{UserBattleStatsResponse => user_stats_data}
        } = _data
      ) do
    user =
      Tornium.Schema.User.from_data(user_profile_data, discord_data: user_discord_data, stats_data: user_stats_data)

    if not faction_exists?(faction_id) do
      # TODO: Pull API data for an update of the faction if the faction is not in the database
      Repo.insert!(%Tornium.Schema.Faction{tid: faction_id}, conflict_target: :tid, on_conflict: :nothing)
    end

    returned_user =
      Repo.insert!(user,
        returning: true,
        conflict_target: :tid,
        on_conflict:
          {:replace,
           [
             :name,
             :level,
             :faction_id,
             :status,
             :last_action,
             :fedded_until,
             :last_refresh,
             :discord_id,
             :strength,
             :defense,
             :speed,
             :dexterity,
             :battlescore
           ]}
      )

    {:ok, returned_user}
  end

  def update_data(
        %{
          Torngen.Client.Path.User.Id.Profile => %{
            UserProfileResponse =>
              %Torngen.Client.Schema.UserProfileResponse{profile: %{faction_id: faction_id}} = user_profile_data
          },
          Torngen.Client.Path.User.Id.Discord => %{UserDiscordResponse => user_discord_data}
        } = _data
      ) do
    user = Tornium.Schema.User.from_data(user_profile_data, discord_data: user_discord_data)

    if not faction_exists?(faction_id) do
      # TODO: Pull API data for an update of the faction if the faction is not in the database
      Repo.insert!(%Tornium.Schema.Faction{tid: faction_id}, conflict_target: :tid, on_conflict: :nothing)
    end

    returned_user =
      Repo.insert!(user,
        returning: true,
        conflict_target: :tid,
        on_conflict:
          {:replace,
           [
             :name,
             :level,
             :faction_id,
             :status,
             :last_action,
             :fedded_until,
             :last_refresh,
             :discord_id
           ]}
      )

    {:ok, returned_user}
  end

  @spec faction_exists?(faction_id :: pos_integer() | nil) :: boolean()
  defp faction_exists?(faction_id) when is_nil(faction_id) do
    # We can say that a faction ID of nil exists as it's not possible to pull data for that
    # faction from the API or insert that faction into the database.
    true
  end

  defp faction_exists?(faction_id) when is_integer(faction_id) do
    Tornium.Schema.Faction
    |> where([f], f.tid == ^faction_id)
    |> Repo.exists?()
  end

  @doc """
  Determine if a user's data should be updated with an API call.

  If the user was last updated more than the minimum period ago, the user should be updated again.
  """
  @spec update_user?(user :: user_id(), minimum_period :: pos_integer()) :: boolean()
  def update_user?({id_type, id} = _user, minimum_period \\ @minimum_update_seconds)
      when id_type in [:torn, :discord] and is_integer(minimum_period) do
    user =
      case id_type do
        :torn ->
          Tornium.Schema.User
          |> select([u], [:last_refresh])
          |> where([u], u.tid == ^id)
          |> first()
          |> Repo.one()

        :discord ->
          Tornium.Schema.User
          |> select([u], [:last_refresh])
          |> where([u], u.discord_id == ^id)
          |> first()
          |> Repo.one()
      end

    case user do
      %Tornium.Schema.User{last_refresh: last_refresh} when is_nil(last_refresh) ->
        true

      %Tornium.Schema.User{last_refresh: last_refresh} ->
        DateTime.diff(DateTime.utc_now(), last_refresh) > minimum_period

      _ ->
        true
    end
  end

  @doc """
  Determine when a user's fedding will end.

  If a user is fallen or permanently fedded, their fedding will expire in the year 9999 as Elixir does not
  support infinite timestamps. If a user is temporarily fedded, it will be the date of the `:until`
  timestamp in the API response. Otherwise, if a user is not fedded, `nil` will be returned.
  """
  @spec fedded_until(user_data :: Torngen.Client.Schema.UserStatus.t() | map()) :: Date.t() | nil
  def fedded_until(%Torngen.Client.Schema.UserStatus{state: "Fallen"} = _user_data) do
    # Since the user is fallen, we'll want to treat them as permanently fedded.
    %Date{
      calendar: Calendar.ISO,
      year: 9999,
      month: 12,
      day: 31
    }
  end

  def fedded_until(%Torngen.Client.Schema.UserStatus{
        state: "Federal",
        description: federal_description,
        until: federal_until
      })
      when is_binary(federal_description) and is_integer(federal_until) do
    permanent_federal? =
      federal_description
      |> String.downcase()
      |> String.contains?("permanently")

    if permanent_federal? do
      # This is the largest date supported by Elixir/OTP
      %Date{
        calendar: Calendar.ISO,
        year: 9999,
        month: 12,
        day: 31
      }
    else
      federal_until
      |> DateTime.from_unix!()
      |> DateTime.to_date()
    end
  end

  def fedded_until(%{"status" => %{"state" => "Fallen"}} = _user_data) do
    # Since the user is fallen, we'll want to treat them as permanently fedded.
    %Date{
      calendar: Calendar.ISO,
      year: 9999,
      month: 12,
      day: 31
    }
  end

  def fedded_until(%{
        "status" => %{"state" => "Federal", "description" => federal_description, "until" => federal_until}
      })
      when is_binary(federal_description) and is_integer(federal_until) do
    permanent_federal? =
      federal_description
      |> String.downcase()
      |> String.contains?("permanently")

    if permanent_federal? do
      # This is the largest date supported by Elixir/OTP
      %Date{
        calendar: Calendar.ISO,
        year: 9999,
        month: 12,
        day: 31
      }
    else
      federal_until
      |> DateTime.from_unix!()
      |> DateTime.to_date()
    end
  end

  def fedded_until(_user_data) do
    # The user is not fedded or fallen
    nil
  end
end
