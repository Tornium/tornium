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

defmodule Tornium.Workers.UserUpdateScheduler do
  @moduledoc """
  A scheduler to spawn `Tornium.Workers.UserUpdate` for the `@max_chunk` least recently updated
  users.

  If a user, that is signed in with an API key, has not been updated for more than an hour, we should
  update that user. If all signed in users have been recently updated, we should update users that
  are not signed in that are the least recently updated.
  """

  import Ecto.Query
  alias Tornium.Repo

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "user"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @max_chunk 100
  @update_niceness 10

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    # TODO: Change f.last_members to the more traditional f.updated_at
    one_hour_ago = DateTime.utc_now() |> DateTime.add(-1, :hour)

    high_priority_users =
      Tornium.Schema.TornKey
      |> where([k], k.default == true and k.disabled == false and k.paused == false and k.access_level >= :limited)
      |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
      |> where([k, u], u.last_refresh < ^one_hour_ago)
      |> select([k, u], k)
      |> limit(@max_chunk)
      |> Repo.all()

    remaining_limit = @max_chunk - length(high_priority_users)

    other_users =
      if remaining_limit > 0 do
        high_priority_user_ids = Enum.map(high_priority_users, & &1.user_id)

        Tornium.Schema.User
        |> where([f], f.tid not in ^high_priority_user_ids)
        |> order_by([f], asc: f.last_refresh)
        |> limit(^remaining_limit)
        |> Repo.all()
      else
        []
      end

    Enum.each(high_priority_users ++ other_users, &scheduler_user_update/1)

    :ok
  end

  @doc """
  Schedule a specific user's data to be updated.

  If a `Tornium.Schema.TornKey` is provided as the user, that specific API key will be used when
  updating the user data of the API key owner.
  """
  @spec scheduler_user_update(user :: Tornium.Schema.TornKey.t() | Tornium.Schema.User.t()) :: term()
  def scheduler_user_update(%Tornium.Schema.TornKey{user_id: user_id} = api_key) when is_integer(user_id) do
    query = Tornium.User.update_query(user_id, api_key, niceness: @update_niceness)

    api_call_id = Ecto.UUID.generate()
    Tornium.API.Store.create(api_call_id, 300)

    Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
      query
      |> Tornex.Scheduler.Bucket.enqueue()
      |> Tornium.API.Store.insert(api_call_id)
    end)

    %{
      api_call_id: api_call_id,
      user_id: user_id,
      api_key_owner: user_id
    }
    |> Tornium.Workers.UserUpdate.new(schedule_in: _seconds = 15)
    |> Oban.insert()
  end

  def scheduler_user_update(%Tornium.Schema.User{tid: user_id} = _user) when is_integer(user_id) do
    %Tornium.Schema.TornKey{user_id: api_key_owner} =
      api_key = Tornium.User.Key.get_by_user(user_id) || Tornium.User.Key.get_random!()

    query = Tornium.User.update_query(user_id, api_key, niceness: @update_niceness)

    api_call_id = Ecto.UUID.generate()
    Tornium.API.Store.create(api_call_id, 300)

    Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
      query
      |> Tornex.Scheduler.Bucket.enqueue()
      |> Tornium.API.Store.insert(api_call_id)
    end)

    %{
      api_call_id: api_call_id,
      user_id: user_id,
      api_key_owner: api_key_owner
    }
    |> Tornium.Workers.UserUpdate.new(schedule_in: _seconds = 15)
    |> Oban.insert()
  end
end
