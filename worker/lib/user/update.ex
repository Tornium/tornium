# Copyright (C) 2021-2023 tiksan
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
  alias Tornium.Repo
  import Ecto.Query

  @minimum_update_seconds 600

  @spec update_user(
          api_user :: Tornium.Schema.User,
          {id_type :: atom(), id :: integer()},
          refresh_existing :: boolean(),
          priority :: integer()
        ) :: {:ok, boolean()} | {:error, Tornium.API.Error.t()}
  def update_user(api_user, {id_type, id}, refresh_existing \\ true, priority \\ 10) do
    if should_update_user?({id_type, id}, refresh_existing) do
      execute_update(api_user, {id_type, id}, priority)
    else
      false
    end
  end

  @spec execute_update(api_user :: Tornium.Schema.User, {id_type :: atom(), id :: integer()}, priority :: integer()) ::
          {:ok, boolean()} | {:error, Tornium.API.Error.t()}
  def execute_update(api_user, {:self, 0}, priority) do
    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "user",
      resource_id: 0,
      selections: "profile,discord,battlestats",
      key: Tornium.User.Key.get_by_user(api_user),
      key_owner: api_user.tid,
      nice: priority
    })
    |> update_user_data(:self)
  end

  def execute_update(api_user, {:tid, id}, priority) do
    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "user",
      resource_id: id,
      selections: "profile,discord",
      key: Tornium.User.Key.get_by_user(api_user),
      key_owner: api_user.tid,
      nice: priority
    })
    |> update_user_data(:tid)
  end

  def execute_update(api_user, {:discord_id, id}, priority) do
    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "user",
      resource_id: id,
      selections: "profile,discord",
      key: Tornium.User.Key.get_by_user(api_user),
      key_owner: api_user.tid,
      nice: priority
    })
    |> update_user_data(:discord_id)
  end

  @spec update_user_data(user_data :: map(), id_type :: atom() | nil) ::
          {:ok, true} | {:error, Tornium.API.Error.t() | nil}
  def update_user_data(%{error: %{code: code, error: error}}, _id_type) do
    {:error, Tornium.API.Error.construct(code, error)}
  end

  def update_user_data(
        %{
          player_id: tid,
          strength: strength,
          defense: defense,
          speed: speed,
          dexterity: dexterity
        } = user_data,
        :self
      ) do
    {:ok, true} = update_user_data(user_data, nil)

    battlescore = :math.sqrt(strength) + :math.sqrt(defense) + :math.sqrt(speed) + :math.sqrt(dexterity)

    {:ok, _} =
      Tornium.Schema.User
      |> where(tid: ^tid)
      |> update(
        set: [strength: ^strength, defense: ^defense, speed: ^speed, dexterity: ^dexterity, battlescore: ^battlescore]
      )
      |> Repo.update()

    {:ok, true}
  end

  def update_user_data(
        %{
          player_id: tid,
          name: name,
          level: level,
          last_action: %{status: status, timestamp: last_action},
          discord: %{discordID: discord_id},
          faction: %{
            faction_id: faction_tid
          }
        } = user_data,
        _id_type
      ) do
    update_user_faction_data(user_data)

    {:ok, last_action} = DateTime.from_unix(last_action)

    {:ok, _} =
      Repo.insert(
        %Tornium.Schema.User{
          tid: tid,
          name: name,
          level: level,
          discord_id: discord_id,
          faction_id: faction_tid,
          status: status,
          last_action: last_action,
          last_refresh: DateTime.utc_now()
        },
        on_conflict: [
          set: [
            name: name,
            level: level,
            discord_id: discord_id,
            faction_id: faction_tid,
            status: status,
            last_action: last_action,
            last_refresh: DateTime.utc_now()
          ]
        ],
        conflict_target: :tid
      )

    update_user_faction_position(user_data)

    {:ok, true}
  end

  def update_user_data(_user_data, _) do
    {:error, nil}
  end

  @spec update_user_faction_data(user_data :: map()) :: boolean()
  defp update_user_faction_data(%{faction: %{faction_id: 0}} = _user_data) do
    false
  end

  defp update_user_faction_data(
         %{faction: %{faction_id: tid, faction_name: name, faction_tag: tag}} =
           _user_data
       ) do
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
         %{player_id: tid, faction: %{position: "Leader", faction_id: faction_tid}} = _user_data
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
         %{player_id: tid, faction: %{position: "Co-leader", faction_id: faction_tid}} = _user_data
       ) do
    {:ok, _} =
      Tornium.Schema.Faction
      |> where(tid: ^faction_tid)
      |> update(set: [coleader_id: ^tid])
      |> Repo.update_all([])

    {:ok, _} =
      Tornium.Schema.User
      |> where(tid: ^tid)
      |> update(set: [faction_position_id: nil, faction_aa: true])
      |> Repo.update_all([])

    true
  end

  defp update_user_faction_position(%{player_id: tid, faction: %{position: position}} = _user_data)
       when position in ["None", "Recruit"] do
    {:ok, _} =
      Tornium.Schema.User
      |> where(tid: ^tid)
      |> update(set: [faction_position_id: nil, faction_aa: false])
      |> Repo.update()

    true
  end

  defp update_user_faction_position(
         %{player_id: tid, faction: %{position: position, faction_id: faction_tid}} = _user_data
       ) do
    position_subquery =
      Tornium.Schema.FactionPosition
      |> select([:pid, :access_fac_api])
      |> where(name: ^position, faction_tid: ^faction_tid)

    {:ok, _} =
      Tornium.Schema.User
      |> join(:inner, [p], p in subquery(position_subquery), on: true)
      |> where(tid: ^tid)
      |> update([p], set: [faction_position_id: p.pid, faction_aa: p.access_fac_api])
      |> Repo.update()

    true
  end

  @spec should_update_user?({id_type :: atom(), id :: integer()}, refresh_existing :: boolean()) :: boolean()
  def should_update_user?({_id_type, _id}, refresh_existing) when refresh_existing == true do
    true
  end

  def should_update_user?({id_type, id}, _refresh_existing) do
    where = [{id_type, id}]
    select = [:last_refresh]
    query = from(Tornium.Schema.User, where: ^where, select: ^select)

    case Repo.one(query) do
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
end
