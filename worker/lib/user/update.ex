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
  Functionality related to updating users' data.
  """

  alias Tornium.Repo
  import Ecto.Query

  @minimum_update_seconds 600

  # TODO: Add documentation for this

  # TODO: Convert update_user to perform pattern matching against the struct instead of the value
  @spec update_user(
          {:user | :key, key_or_user :: Tornium.Schema.User.t() | Tornium.Schema.TornKey.t()},
          {id_type :: :tid | :discord_id | :self, id :: integer()},
          refresh_existing :: boolean(),
          priority :: integer()
        ) :: {:ok, boolean()} | {:error, Tornium.API.Error.t()}
  def update_user({type, key_or_user}, {id_type, id}, refresh_existing \\ true, priority \\ 10) do
    if should_update_user?({id_type, id}, refresh_existing) do
      execute_update({type, key_or_user}, {id_type, id}, priority)
    else
      false
    end
  end

  # TODO: Convert execute_update to perform pattern matching against the struct instead of the value
  @spec execute_update(
          {:user | :key, key_or_user :: Tornium.Schema.User.t() | Tornium.Schema.TornKey.t()},
          {id_type :: atom(), id :: integer()},
          priority :: integer()
        ) ::
          {:ok, boolean()} | {:error, Tornium.API.Error.t()}
  def execute_update({:user, key_or_user}, {id_type, id}, priority) do
    case Tornium.User.Key.get_by_user(key_or_user) do
      nil -> {:error, Tornium.API.Error.construct(2, "Incorrect Key")}
      api_key -> execute_update({:key, api_key}, {id_type, id}, priority)
    end
  end

  def execute_update({:key, key_or_user}, {:self, 0}, priority) do
    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "user",
      resource_id: 0,
      selections: ["profile", "discord", "battlestats"],
      key: key_or_user.api_key,
      key_owner: key_or_user.user_id,
      nice: priority
    })
    |> update_user_data(:self)
  end

  def execute_update({:key, key_or_user}, {:tid, id}, priority) do
    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "user",
      resource_id: id,
      selections: ["profile", "discord"],
      key: key_or_user.api_key,
      key_owner: key_or_user.user_id,
      nice: priority
    })
    |> update_user_data(:tid)
  end

  def execute_update({:key, key_or_user}, {:discord_id, id}, priority) do
    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "user",
      resource_id: id,
      selections: ["profile", "discord"],
      key: key_or_user.api_key,
      key_owner: key_or_user.user_id,
      nice: priority
    })
    |> update_user_data(:discord_id)
  end

  @spec update_user_data(user_data :: map(), id_type :: atom() | nil) ::
          {:ok, true} | {:error, Tornium.API.Error.t() | nil}
  def update_user_data(%{"error" => %{"code" => code, "error" => error}}, _id_type) do
    {:error, Tornium.API.Error.construct(code, error)}
  end

  def update_user_data(
        %{
          "player_id" => tid,
          "strength" => strength,
          "defense" => defense,
          "speed" => speed,
          "dexterity" => dexterity
        } = user_data,
        :self
      ) do
    {:ok, true} = update_user_data(user_data, nil)

    battlescore = :math.sqrt(strength) + :math.sqrt(defense) + :math.sqrt(speed) + :math.sqrt(dexterity)

    {1, _} =
      Tornium.Schema.User
      |> where(tid: ^tid)
      |> update(
        set: [strength: ^strength, defense: ^defense, speed: ^speed, dexterity: ^dexterity, battlescore: ^battlescore]
      )
      |> Repo.update_all([])

    {:ok, true}
  end

  def update_user_data(
        %{
          "player_id" => tid,
          "name" => name,
          "level" => level,
          "last_action" => %{"status" => status, "timestamp" => last_action},
          "discord" => %{"discordID" => discord_id},
          "faction" => %{
            "faction_id" => faction_tid
          }
        } = user_data,
        _id_type
      ) do
    update_user_faction_data(user_data)

    {:ok, last_action} = DateTime.from_unix(last_action)

    # TODO: Replace set in the on_conflict clause with replace
    {:ok, _} =
      Repo.insert(
        %Tornium.Schema.User{
          tid: tid,
          name: name,
          level: level,
          discord_id: Tornium.Utils.string_to_integer(discord_id),
          faction_id: faction_tid,
          status: status,
          last_action: last_action,
          fedded_until: fedded_until(user_data),
          last_refresh: DateTime.utc_now()
        },
        on_conflict: [
          set: [
            name: name,
            level: level,
            discord_id: Tornium.Utils.string_to_integer(discord_id),
            faction_id: faction_tid,
            status: status,
            last_action: last_action,
            fedded_until: fedded_until(user_data),
            last_refresh: DateTime.utc_now()
          ]
        ],
        conflict_target: :tid
      )

    update_user_faction_position(user_data)

    {:ok, true}
  end

  @spec update_user_faction_data(user_data :: map()) :: boolean()
  defp update_user_faction_data(%{"faction" => %{"faction_id" => 0}} = _user_data) do
    false
  end

  defp update_user_faction_data(
         %{"faction" => %{"faction_id" => tid, "faction_name" => name, "faction_tag" => tag}} =
           _user_data
       ) do
    # TODO: Replace set in the on_conflict clause with replace
    Repo.insert(
      %Tornium.Schema.Faction{
        tid: tid,
        name: name,
        tag: tag
      },
      on_conflict: [
        set: [name: name, tag: tag]
      ],
      conflict_target: :tid
    )

    true
  end

  @spec update_user_faction_position(user_data :: map()) :: boolean()
  defp update_user_faction_position(
         %{"player_id" => tid, "faction" => %{"position" => "Leader", "faction_id" => faction_tid}} = _user_data
       ) do
    {1, _} =
      Tornium.Schema.Faction
      |> where(tid: ^faction_tid)
      |> update(set: [leader_id: ^tid])
      |> Repo.update_all([])

    {1, _} =
      Tornium.Schema.User
      |> where(tid: ^tid)
      |> update(set: [faction_position_id: nil, faction_aa: true])
      |> Repo.update_all([])

    true
  end

  defp update_user_faction_position(
         %{"player_id" => tid, "faction" => %{"position" => "Co-leader", "faction_id" => faction_tid}} = _user_data
       ) do
    {1, _} =
      Tornium.Schema.Faction
      |> where(tid: ^faction_tid)
      |> update(set: [coleader_id: ^tid])
      |> Repo.update_all([])

    {1, _} =
      Tornium.Schema.User
      |> where(tid: ^tid)
      |> update(set: [faction_position_id: nil, faction_aa: true])
      |> Repo.update_all([])

    true
  end

  defp update_user_faction_position(%{"player_id" => tid, "faction" => %{"position" => position}} = _user_data)
       when position in ["None", "Recruit"] do
    {1, _} =
      Tornium.Schema.User
      |> where(tid: ^tid)
      |> update(set: [faction_position_id: nil, faction_aa: false])
      |> Repo.update_all([])

    true
  end

  defp update_user_faction_position(
         %{"player_id" => tid, "faction" => %{"position" => position, "faction_id" => faction_tid}} = _user_data
       ) do
    position_subquery =
      Tornium.Schema.FactionPosition
      |> select([:pid, :permissions])
      |> select([p], %{pid: p.pid, has_aa: "Faction API Access" in p.permissions})
      |> where([p], p.name == ^position)
      |> where([p], p.faction_id == ^faction_tid)
      |> limit(1)

    {count, _} =
      Tornium.Schema.User
      |> join(:inner, [u], p in subquery(position_subquery), on: u.faction_position_id == p.pid)
      |> where([u, p], u.tid == ^tid)
      |> update([u, p], set: [faction_position_id: p.pid, faction_aa: p.has_aa])
      |> Repo.update_all([])

    case count do
      0 -> false
      _ -> true
    end
  end

  @doc """
  Determine if a user's data should be updated.

  If `:refresh_existing` is true, the user's data should be updated regardless of other parameters. Otherwise,
  the user should be updated when the user was never last updated or was last updated more than
  `@minimum_update_seconds` seconds ago.
  """
  @spec should_update_user?(user_id :: {id_type :: atom(), id :: integer()}, refresh_existing :: boolean()) :: boolean()
  def should_update_user?({_id_type, _id} = _user_id, refresh_existing) when refresh_existing == true do
    true
  end

  def should_update_user?({id_type, id}, _refresh_existing) do
    user =
      Tornium.Schema.User
      |> select([:last_refresh])
      |> where(^id_type == ^id)
      |> first()
      |> Repo.one()

    case user do
      nil ->
        true

      %Tornium.Schema.User{last_refresh: last_refresh} when is_nil(last_refresh) ->
        true

      %Tornium.Schema.User{last_refresh: last_refresh} ->
        DateTime.diff(DateTime.utc_now(), last_refresh) > @minimum_update_seconds

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
