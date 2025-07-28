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

  @doc """
  Fetch a list of admins' Discord IDs for a guild.

  If a map of guild roles is not provided, the roles will be fetched from the API. The guild roles are
  filtered to determine a subset representing all roles with the administrator permission. Using this
  subset of roles, `do_fetch_admins/3` can recursively determine if there is a union between the subset
  and users' roles to determine a list of admin users.

  ## Parameters:
    - guild_id: ID of the Discord guild
    - roles: list of all roles in the Discord guild

  ## Returns
    - List of Discord user IDs with admin permissions
  """
  @spec fetch_admins(
          guild_id :: non_neg_integer(),
          roles :: [Nostrum.Struct.Guild.Role.t()] | nil
        ) :: [non_neg_integer()]
  def fetch_admins(guild_id, roles \\ nil)

  def fetch_admins(guild_id, roles) when is_integer(guild_id) and is_nil(roles) do
    {:ok, fetched_roles} = Nostrum.Api.Guild.roles(guild_id)

    fetch_admins(guild_id, fetched_roles)
  end

  def fetch_admins(guild_id, roles) when is_integer(guild_id) and is_list(roles) do
    admin_roles =
      roles
      |> Enum.filter(fn %Nostrum.Struct.Guild.Role{permissions: role_permissions} ->
        role_permissions
        |> Nostrum.Permission.from_bitset()
        |> Enum.member?(:administrator)
      end)
      |> Enum.map(fn %Nostrum.Struct.Guild.Role{id: role_id} -> role_id end)
      |> MapSet.new()

    guild_id
    |> do_fetch_admins(admin_roles)
    |> Enum.uniq()
  end

  @spec do_fetch_admins(
          guild_id :: non_neg_integer(),
          admin_roles :: MapSet.t(Tornium.Discord.role()),
          largest_member_id :: non_neg_integer()
        ) :: [non_neg_integer()]
  defp do_fetch_admins(guild_id, %MapSet{} = admin_roles, largest_member_id \\ 0)
       when is_integer(guild_id) do
    {:ok, members} = Nostrum.Api.Guild.members(guild_id, %{limit: 1000, after: largest_member_id})

    largest_member_id =
      members
      |> Enum.max_by(fn %Nostrum.Struct.Guild.Member{user_id: user_id} -> user_id end)
      |> max(largest_member_id)

    admins =
      members
      |> Enum.filter(fn %Nostrum.Struct.Guild.Member{roles: user_roles} ->
        # Check if the user has a role known to have the admin permission
        user_roles
        |> MapSet.new()
        |> MapSet.disjoint?(admin_roles)
        |> Kernel.not()
      end)
      |> Enum.map(fn %Nostrum.Struct.Guild.Member{user_id: user_id} -> user_id end)

    if length(members) >= 1000 do
      [do_fetch_admins(guild_id, admin_roles, largest_member_id) | admins]
    else
      admins
    end
  end
end
