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

defmodule Tornium.Guild do
  import Ecto.Query

  alias Tornium.Repo

  @doc """
  Retrieve all API keys of a server's admins

  ## Parameters
    - guild: The guild ID or an Ecto struct of the server

  ## Returns
    - List of API keys (Tornium.Schema.TornKey)
  """
  @spec get_admin_keys(guild :: integer() | Tornium.Schema.Server.t()) :: List
  def get_admin_keys(guild) when is_integer(guild) do
    # TODO: Convert to a single DB query
    guild = Repo.get(Tornium.Schema.Server, guild)
    get_admin_keys(guild)
  end

  def get_admin_keys(guild) when is_nil(guild) or Kernel.length(guild.admins) == 0 do
    []
  end

  def get_admin_keys(%Tornium.Schema.Server{} = guild) do
    Tornium.Schema.TornKey
    |> where(
      [key],
      key.user_id in ^guild.admins and key.disabled == false and key.paused == false and key.default == true
    )
    |> Repo.all()
  end

  @doc """
  Retrieve a random API key of a server's admins

  ## Parameters
    - guild: The guild ID or an Ecto struct of the server

  ## Returns
    - API key if there are more than one API keys available
    - nil if there are no API keys available
  """
  @spec get_random_admin_key(guild :: integer() | Tornium.Schema.Server.t()) :: Tornium.Schema.TornKey.t() | nil
  def get_random_admin_key(guild) when is_integer(guild) do
    Repo.get(Tornium.Schema.Server, guild)
    |> get_admin_keys()
    |> select_random_key()
  end

  def get_random_admin_key(%Tornium.Schema.Server{} = guild) do
    # TODO: Convert to a DB query that doesn't require querying all admin users and their keys
    get_admin_keys(guild)
    |> select_random_key()
  end

  @spec select_random_key(api_keys :: List) :: Tornium.Schema.TornKey.t() | nil
  defp select_random_key(api_keys) when Kernel.length(api_keys) == 0 do
    nil
  end

  defp select_random_key(api_keys) do
    Enum.random(api_keys)
  end
end
