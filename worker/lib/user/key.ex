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

defmodule Tornium.User.Key do
  @moduledoc """
  Utilities to fetch API keys for certain circumstances.
  """

  import Ecto.Query
  alias Tornium.Repo

  @doc """
  Get the default API key for a specific user or a specific user ID.
  """
  @spec get_by_user(user :: Tornium.Schema.User.t() | non_neg_integer()) :: Tornium.Schema.TornKey.t() | nil
  def get_by_user(%Tornium.Schema.User{} = user) do
    pid = Process.whereis(Tornium.User.KeyStore)
    get_by_user(user, pid)
  end

  def get_by_user(user_id) when is_integer(user_id) do
    pid = Process.whereis(Tornium.User.KeyStore)
    get_by_user(user_id, pid)
  end

  @spec get_by_user(user :: Tornium.Schema.User.t() | non_neg_integer(), pid :: pid()) ::
          Tornium.Schema.TornKey.t() | nil
  def get_by_user(%Tornium.Schema.User{tid: user_id} = _user, pid) when not is_nil(pid) do
    get_by_user(user_id, pid)
  end

  def get_by_user(user_id, pid) when is_integer(user_id) and not is_nil(pid) do
    case Tornium.User.KeyStore.get(pid, user_id) do
      nil ->
        where = [user_id: user_id, paused: false, disabled: false, default: true]
        query = from(Tornium.Schema.TornKey, where: ^where)
        torn_key = Repo.one(query)
        Tornium.User.KeyStore.put(pid, user_id, torn_key)
        torn_key

      torn_key ->
        torn_key
    end
  end

  @doc """
  Get a random API key to pull public Torn data.

  The owner of the API key must have `:public_data_enabled` set to true in their `Tornium.Schema.UserSettings`
  for their API key to be used for this.
  """
  @spec get_random!() :: Tornium.Schema.TornKey.t()
  def get_random!() do
    get_random_query()
    |> first()
    |> Repo.one!()
  end

  @doc """
  Get random API keys to pull public Torn data.

  The owner of the API keys must have `:public_data_enabled` set to true in their `Tornium.Schema.UserSettings`
  for their API key to be used for this.

  ## Options
    * `:limit` - The maximum number of API keys to return (default: `10`)
  """
  @spec get_random(opts :: keyword()) :: [Tornium.Schema.TornKey.t()]
  def get_random(opts \\ []) do
    limit = Keyword.get(opts, :limit, 10)

    get_random_query()
    |> limit(^limit)
    |> Repo.all()
  end

  defp get_random_query() do
    Tornium.Schema.TornKey
    |> where([k], k.default == true and k.disabled == false and k.paused == false)
    |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
    |> join(:inner, [k, u], s in assoc(u, :settings), on: s.guid == u.settings_id)
    |> where([k, u, s], s.public_data_enabled == true)
    |> order_by([k, u, s], fragment("RANDOM()"))
  end
end
