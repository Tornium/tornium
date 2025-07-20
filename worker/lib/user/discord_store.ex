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

defmodule Tornium.User.DiscordStore do
  @moduledoc """
  Agent to cache Discord IDs of users.
  """

  # TODO: Add documentation
  # TODO: Test this

  use Agent
  import Ecto.Query
  alias Tornium.Repo

  # 7 days
  @ttl 604_800

  @spec start_link(opts :: Keyword.t()) :: Agent.on_start()
  def start_link(opts \\ [name: Tornium.User.KeyStore]) do
    Agent.start_link(fn -> %{} end, opts)
  end

  @spec get(user_id :: non_neg_integer()) :: non_neg_integer() | nil
  def get(user_id) when is_integer(user_id) do
    case get(Tornium.User.DiscordStore, user_id) do
      discord_id when is_integer(discord_id) -> nil
      _ -> put(user_id)
    end
  end

  @spec put(user_id :: non_neg_integer()) :: non_neg_integer() | nil
  def put(user_id) when is_integer(user_id) do
    discord_id =
      Tornium.Schema.User
      |> select([u], u.discord_id)
      |> where([u], u.tid == ^user_id)
      |> Repo.one()

    case discord_id do
      nil ->
        nil

      %Tornium.Schema.User{discord_id: user_discord_id} ->
        put(Tornium.User.DiscordStore, user_id, user_discord_id)
        user_discord_id
    end
  end

  @spec put(
          pid :: pid(),
          user_id :: non_neg_integer(),
          user_discord_id :: non_neg_integer() | nil,
          ttl :: non_neg_integer()
        ) :: :ok | :error
  defp put(pid, user_id, user_discord_id, ttl \\ @ttl)

  defp put(_pid, _user_id, user_discord_id, _ttl) when is_nil(user_discord_id) do
    # We don't want to cache nil Discord IDs in case the user verifies within the TTL of the cache.
    :error
  end

  defp put(pid, user_id, user_discord_id, ttl) when is_integer(user_id) and is_integer(user_discord_id) do
    Agent.update(
      pid,
      &Map.put(&1, user_id, %{user_discord_id: user_discord_id, expire: DateTime.add(DateTime.utc_now(), ttl, :second)})
    )
  end

  @spec get(pid :: pid(), user_id :: integer()) :: Tornium.Schema.TornKey.t() | :expired | nil
  defp get(pid, user_id) when is_integer(user_id) do
    case Agent.get(pid, &Map.get(&1, user_id), :infinity) do
      %{user_discord_id: user_discord_id, expire: expire} ->
        if DateTime.after?(DateTime.utc_now(), expire) do
          Agent.update(pid, &Map.delete(&1, user_id))
          :expired
        else
          user_discord_id
        end

      nil ->
        nil
    end
  end
end
