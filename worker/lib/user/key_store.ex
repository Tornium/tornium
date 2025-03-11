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
  use Agent

  # 5 minutes
  @ttl 300

  def start_link(opts \\ [name: Tornium.User.KeyStore]) do
    Agent.start_link(fn -> %{} end, opts)
  end

  @spec put(pid :: pid(), key :: integer(), value :: Tornium.Schema.TornKey.t() | nil, ttl :: integer()) :: :ok | :error
  def put(pid, key, value, ttl \\ @ttl)

  def put(_pid, _key, value, _ttl) when is_nil(value) do
    :error
  end

  def put(pid, key, %Tornium.Schema.TornKey{} = value, ttl) do
    Agent.update(pid, &Map.put(&1, key, %{value: value, expire: DateTime.add(DateTime.utc_now(), ttl, :second)}))
  end

  @spec get(pid :: pid(), key :: integer()) :: Tornium.Schema.TornKey.t() | nil
  def get(pid, key) do
    case Agent.get(pid, &Map.get(&1, key), :infinity) do
      %{value: value, expire: expire} ->
        if DateTime.after?(DateTime.utc_now(), expire) do
          nil
        else
          value
        end

      nil ->
        nil
    end
  end
end
