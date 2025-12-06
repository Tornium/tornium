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
  Utilities to get API keys of users.

  This will cache the API key in the `KeyStore`.
  """

  import Ecto.Query
  alias Tornium.Repo

  @doc """
  Get the default API key for a specific user or a specific user ID.
  """
  @spec get_by_user(user :: Tornium.Schema.User.t() | pos_integer()) :: Tornium.Schema.TornKey.t() | nil
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
  Get a random user's default API key.
  """
  @spec get_random_key() :: Tornium.Schema.TornKey.t()
  def get_random_key() do
    Tornium.Schema.TornKey
    |> where([k], k.paused == false and k.disabled == false and k.default == true)
    |> order_by(fragment("RANDOM()"))
    |> first()
    |> Repo.one!()
  end
end
