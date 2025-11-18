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

defmodule Tornium.User.KeyStore do
  @moduledoc """
  Agent to cache API keys.
  """

  use Agent

  @doc """
  Start the API key cache.
  """
  @spec start_link(opts :: keyword()) :: Agent.on_start()
  def start_link(opts \\ [name: Tornium.User.KeyStore]) do
    Agent.start_link(fn -> %{} end, opts)
  end

  @doc """
  Insert the API key for a user ID into the cache.
  """
  @spec put(pid :: pid(), user_id :: pos_integer(), api_key :: Tornium.Schema.TornKey.t() | nil, ttl :: Duration.t()) ::
          :ok | :error
  def put(pid, user_id, api_key, ttl \\ %Duration{minute: 5})

  def put(_pid, _user_id, api_key, %Duration{} = _ttl) when is_nil(api_key) do
    :error
  end

  def put(pid, user_id, %Tornium.Schema.TornKey{} = api_key, %Duration{} = ttl) when is_integer(user_id) do
    Agent.update(pid, &Map.put(&1, user_id, %{api_key: api_key, expire: DateTime.shift(DateTime.utc_now(), ttl)}))
  end

  @doc """
  Get an API key for a user ID if it can be found in the cache and is not expired.
  """
  @spec get(pid :: Agent.agent(), user_id :: integer()) :: Tornium.Schema.TornKey.t() | nil
  def get(pid, user_id) do
    case Agent.get(pid, &Map.get(&1, user_id), :infinity) do
      %{api_key: api_key, expire: expire} ->
        if DateTime.after?(DateTime.utc_now(), expire) do
          nil
        else
          api_key
        end

      nil ->
        nil
    end
  end
end
