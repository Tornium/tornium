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

defmodule Tornium.Guild.Verify do
  alias Tornium.Repo
  import Ecto.Query
  require Logger

  @doc """
  Handle verification of a user in a server

  ## Parameters

    - guild_id: ID of the guild the user should be verified for
    - member: Nostrum struct of the Discord member of the user

  ## Returns
    - OK with the updated member struct
    - Error with the error reason
  """
  @spec handle(guild_id :: integer(), member :: Nostrum.Struct.Guild.Member.t()) ::
          {:ok, Nostrum.Struct.Guild.Member.t()}
          | {:error, Nostrum.Error.ApiError | Tornium.API.Error | :unverified | :nochanges | :config}
  def handle(guild_id, member) do
    case Repo.get(Tornium.Schema.Server, guild_id) do
      nil ->
        {:error, :config}

      %Tornium.Schema.Server{} = guild ->
        api_key = Tornium.Guild.get_random_admin_key(guild)
        handle_guild(guild, api_key, member) |> IO.inspect()
    end
  end

  @spec handle_guild(
          guild :: Tornium.Schema.Server.t() | nil,
          api_key :: Tornium.Schema.TornKey | nil,
          member :: Nostrum.Struct.Guild.Member.t()
        ) ::
          {:ok, Nostrum.Struct.Guild.Member.t()}
          | {:error, Nostrum.Error.ApiError | Tornium.API.Error | :unverified | :nochanges | :config | :api_key}
  defp handle_guild(guild, api_key, %Nostrum.Struct.Guild.Member{} = _member) when is_nil(guild) do
    {:error, :config}
  end

  defp handle_guild(guild, api_key, %Nostrum.Struct.Guild.Member{} = _member) when is_nil(api_key) do
    {:error, :api_key}
  end

  defp handle_guild(
         %Tornium.Schema.Server{} = guild,
         %Tornium.Schema.TornKey{} = api_key,
         %Nostrum.Struct.Guild.Member{} = member
       ) do
    case Tornium.Guild.Verify.Config.validate(guild) do
      {:error, reason} ->
        Logger.debug(["Failed to verify user ", member.user_id, " in guild ", guild.sid, " on join due to ", reason])
        {:error, :config}

      %Tornium.Guild.Verify.Config{} = config ->
        Tornium.User.update_user({:key, api_key}, {:discord_id, member.user_id}, true, 0)
        |> build_changes(config, member)
        |> IO.inspect()
        |> perform_changes(guild, member)
        |> IO.inspect()
    end
  end

  @spec validate_changes_made(new_roles_nick :: map(), original_roles :: List, original_nick :: String) ::
          map() | :nochanges
  defp validate_changes_made(%{roles: roles, nick: nick} = new_roles_nick, original_roles, original_nick) do
    if roles == original_roles do
      ^new_roles_nick = Map.delete(new_roles_nick, :roles)
    end

    if nick == original_nick do
      ^new_roles_nick = Map.delete(new_roles_nick, :nick)
    end

    if Kernel.map_size(new_roles_nick) == 0 do
      :nochanges
    else
      new_roles_nick
    end
  end

  @spec build_changes(
          {:ok, boolean()} | {:error, Tornium.API.Error.t()},
          config :: Tornium.Guild.Verify.Config.t(),
          member :: Nostrum.Struct.Guild.Member.t()
        ) :: Map | Tornium.API.Error.t() | :unverified | :nochanges
  defp build_changes({:ok, _}, config, %Nostrum.Struct.Guild.Member{
         roles: roles,
         nick: nick,
         user_id: discord_id
       }) do
    user =
      Tornium.Schema.User
      |> where([u], u.discord_id == ^discord_id)
      |> Repo.one()

    case user do
      nil ->
        :unverified

      user ->
        %{roles: roles, nick: nick}
        |> Tornium.Guild.Verify.Logic.remove_invalid_faction_roles(user, config)
        |> Tornium.Guild.Verify.Logic.remove_invalid_faction_position_roles(user, config)
        |> Tornium.Guild.Verify.Logic.set_verified_name(user, config)
        |> Tornium.Guild.Verify.Logic.set_verified_roles(user, config)
        |> Tornium.Guild.Verify.Logic.set_faction_roles(user, config)
        |> Tornium.Guild.Verify.Logic.set_faction_position_roles(user, config)
        |> validate_changes_made(roles, nick)
    end
  end

  defp build_changes({:error, %Tornium.API.Error{code: code} = _error}, _config, _member) when code == 6 do
    :unverified
  end

  defp build_changes({:error, %Tornium.API.Error{} = error}, _config, _member) do
    error
  end

  @spec perform_changes(
          changeset :: Map | Tornium.API.Error.t() | atom(),
          guild :: Tornium.Schema.Server.t(),
          member :: Nostrum.Struct.Guild.Member.t()
        ) ::
          {:ok, Nostrum.Struct.Guild.Member.t()}
          | {:error, Nostrum.Error.ApiError | Tornium.API.Error | :unverified | :nochanges}
  defp perform_changes(:unverified, _guild, _member) do
    {:error, :unverified}
  end

  defp perform_changes(:nochanges, _guild, _member) do
    {:error, :nochanges}
  end

  defp perform_changes(%Tornium.API.Error{} = error, _guild, _member) do
    {:error, error}
  end

  defp perform_changes(
         %{roles: roles, nick: nick} = _changeset,
         %Tornium.Schema.Server{sid: guild_id} = _guild,
         %Nostrum.Struct.Guild.Member{user_id: member_id} = _member
       ) do
    Nostrum.Api.modify_guild_member(guild_id, member_id, %{nick: nick, roles: roles}, "Tornium on-join verification")
  end
end
