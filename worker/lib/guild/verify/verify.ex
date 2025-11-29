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

defmodule Tornium.Guild.Verify do
  alias Tornium.Repo
  import Ecto.Query
  require Logger

  # TODO: Comment the private methods
  # TODO: Combine some of the types with pre-defined types

  @doc """
  Handle verification of a user in a server

  ## Parameters
    - guild: ID of the guild the user should be verified for
    - member: Nostrum struct of the Discord member of the user

  ## Returns
    - OK with the updated member struct
    - Error with the error reason
  """
  @spec handle(guild :: integer() | Tornium.Schema.Server.t(), member :: Nostrum.Struct.Guild.Member.t()) ::
          {:ok, Nostrum.Struct.Guild.Member.t(), Tornium.Schema.Server.t()}
          | {:error,
             Nostrum.Error.ApiError
             | Tornium.API.Error
             | :unverified
             | :nochanges
             | :api_key
             | :exclusion_role
             | {:config, String.t()}, Tornium.Schema.Server.t()}
  def handle(guild, %Nostrum.Struct.Guild.Member{} = member) when is_integer(guild) do
    Tornium.Schema.Server
    |> Repo.get(guild)
    |> handle(member)
  end

  def handle({:error, error}, _member) do
    # Error passthrough from possible validation of server configuration
    {:error, error}
  end

  def handle(guild, %Nostrum.Struct.Guild.Member{} = _member) when is_nil(guild) do
    {:error, {:config, "invalid guild ID"}, nil}
  end

  def handle(%Tornium.Schema.Server{} = guild, %Nostrum.Struct.Guild.Member{} = member) do
    if MapSet.size(MapSet.intersection(MapSet.new(member.roles), MapSet.new(guild.exclusion_roles))) > 0 do
      # Member has at least one exclusion role and should be skipped
      {:error, :exclusion_role, guild}
    else
      api_key = Tornium.Guild.get_random_admin_key(guild)

      case handle_guild(guild, api_key, member) do
        {:ok, %Nostrum.Struct.Guild.Member{} = member} -> {:ok, member, guild}
        {:error, error} -> {:error, error, guild}
      end
    end
  end

  defp validate_on_join(%Tornium.Schema.Server{gateway_verify_enabled: false} = _guild) do
    {:error, {:config, "gateway verification disabled"}}
  end

  defp validate_on_join(%Tornium.Schema.Server{gateway_verify_enabled: true} = guild) do
    guild
  end

  defp validate_on_join(guild) when is_nil(guild) do
    guild
  end

  @doc """
  Handle verification of a user in a server when the user joins the server

  ## Parameters
    - guild_id: ID of the guild the user should be verified for
    - member: Nostrum struct of the Discord member of the user

  ## Returns
    - OK with the updated member struct
    - Error with the error reason
  """
  @spec handle_on_join(guild_id :: integer(), member :: Nostrum.Struct.Guild.Member.t()) ::
          {:ok, Nostrum.Struct.Guild.Member.t(), Tornium.Schema.Server.t()}
          | {:error,
             Nostrum.Error.ApiError
             | Tornium.API.Error
             | :unverified
             | :nochanges
             | :api_key
             | :exclusion_role
             | {:config, String.t()}, Tornium.Schema.Server.t()}
  def handle_on_join(guild_id, member) when is_integer(guild_id) do
    Repo.get(Tornium.Schema.Server, guild_id)
    |> validate_on_join()
    |> handle(member)
  end

  # TODO: Rename handle_guild to be more descriptive
  @spec handle_guild(
          guild :: Tornium.Schema.Server.t(),
          api_key :: Tornium.Schema.TornKey | nil,
          member :: Nostrum.Struct.Guild.Member.t()
        ) ::
          {:ok, Nostrum.Struct.Guild.Member.t()}
          | {:error,
             Nostrum.Error.ApiError.t()
             | Tornium.API.Error.t()
             | :unverified
             | :nochanges
             | :api_key
             | {:config, String.t()}}
  defp handle_guild(_guild, api_key, %Nostrum.Struct.Guild.Member{} = _member) when is_nil(api_key) do
    {:error, :api_key}
  end

  defp handle_guild(
         %Tornium.Schema.Server{} = guild,
         %Tornium.Schema.TornKey{} = api_key,
         %Nostrum.Struct.Guild.Member{} = member
       ) do
    case Tornium.Guild.Verify.Config.validate(guild) do
      {:error, reason} when is_binary(reason) ->
        {:error, {:config, String.downcase(reason)}}

      %Tornium.Guild.Verify.Config{} = config ->
        Tornium.User.update_user({:key, api_key}, {:discord_id, member.user_id}, true, 0)
        |> build_changes(config, member)
        |> perform_changes(guild, member)
    end
  end

  @spec validate_changes_made(new_roles_nick :: map(), original_roles :: List, original_nick :: String) ::
          map() | :nochanges
  defp validate_changes_made(%{roles: roles, nick: nick} = _new_roles_nick, original_roles, original_nick) do
    patched_map =
      %{roles: MapSet.to_list(roles), nick: nick}
      |> then(fn patched_map -> if roles == original_roles, do: Map.delete(patched_map, :roles), else: patched_map end)
      |> then(fn patched_map -> if nick == original_nick, do: Map.delete(patched_map, :nick), else: patched_map end)

    if Kernel.map_size(patched_map) == 0 do
      :nochanges
    else
      patched_map
    end
  end

  @spec build_changes(
          {:ok, boolean()} | {:error, Tornium.API.Error.t()},
          config :: Tornium.Guild.Verify.Config.t(),
          member :: Nostrum.Struct.Guild.Member.t()
        ) :: {:verified, map()} | Tornium.API.Error.t() | {:unverified, map()} | :nochanges
  defp build_changes({:ok, _}, config, %Nostrum.Struct.Guild.Member{
         roles: roles,
         nick: nick,
         user_id: discord_id
       }) do
    user =
      Tornium.Schema.User
      |> join(:left, [u], f in assoc(u, :faction), on: f.tid == u.faction_id)
      |> where([u, f], u.discord_id == ^discord_id)
      |> preload([u, f], faction: f)
      |> Repo.one()

    case user do
      nil ->
        changes =
          %{roles: MapSet.new(roles), nick: nick}
          |> Tornium.Guild.Verify.Logic.remove_invalid_verified_roles(config, user)
          |> Tornium.Guild.Verify.Logic.remove_invalid_faction_roles(config, user)
          |> Tornium.Guild.Verify.Logic.remove_invalid_faction_position_roles(config, user)
          |> Tornium.Guild.Verify.Logic.set_unverified_roles(config, user)
          |> Map.update!(:roles, &MapSet.to_list/1)

        {:unverified, changes}

      user ->
        changes =
          %{roles: MapSet.new(roles), nick: nick}
          |> Tornium.Guild.Verify.Logic.remove_invalid_unverified_roles(config, user)
          |> Tornium.Guild.Verify.Logic.remove_invalid_faction_roles(config, user)
          |> Tornium.Guild.Verify.Logic.remove_invalid_faction_position_roles(config, user)
          |> Tornium.Guild.Verify.Logic.set_verified_name(config, user)
          |> Tornium.Guild.Verify.Logic.set_verified_roles(config, user)
          |> Tornium.Guild.Verify.Logic.set_faction_roles(config, user)
          |> Tornium.Guild.Verify.Logic.set_faction_position_roles(config, user)
          |> validate_changes_made(roles, nick)

        {:verified, changes}
    end
  end

  defp build_changes(
         {:error, %Tornium.API.Error{code: code} = _error},
         %Tornium.Guild.Verify.Config{} = config,
         %Nostrum.Struct.Guild.Member{
           roles: roles,
           nick: nick
         }
       )
       when code == 6 do
    changes =
      %{roles: MapSet.new(roles), nick: nick}
      |> Tornium.Guild.Verify.Logic.remove_invalid_verified_roles(config, nil)
      |> Tornium.Guild.Verify.Logic.remove_invalid_faction_roles(config, nil)
      |> Tornium.Guild.Verify.Logic.remove_invalid_faction_position_roles(config, nil)
      |> Tornium.Guild.Verify.Logic.set_unverified_roles(config, nil)
      |> Map.update!(:roles, &MapSet.to_list/1)

    {:unverified, changes}
  end

  defp build_changes({:error, %Tornium.API.Error{} = error}, _config, _member) do
    error
  end

  @spec perform_changes(
          changeset :: {:verified, map()} | {:unverified, map()} | :nochanges | Tornium.API.Error.t(),
          guild :: Tornium.Schema.Server.t(),
          member :: Nostrum.Struct.Guild.Member.t()
        ) ::
          {:ok, Nostrum.Struct.Guild.Member.t()}
          | {:error, Nostrum.Error.ApiError.t() | Tornium.API.Error.t() | :unverified | :nochanges}
  defp perform_changes(
         {:unverified, %{roles: roles, nick: nick}} = _changeset,
         %Tornium.Schema.Server{sid: guild_id} = _guild,
         %Nostrum.Struct.Guild.Member{user_id: member_id} = _member
       )
       when is_list(roles) do
    Nostrum.Api.Guild.modify_member(guild_id, member_id, %{nick: nick, roles: roles})
    {:error, :unverified}
  end

  defp perform_changes(:nochanges, _guild, _member) do
    {:error, :nochanges}
  end

  defp perform_changes(%Tornium.API.Error{} = error, _guild, _member) do
    {:error, error}
  end

  defp perform_changes(
         {:verified, %{roles: roles, nick: nick} = _changeset},
         %Tornium.Schema.Server{sid: guild_id} = _guild,
         %Nostrum.Struct.Guild.Member{user_id: member_id} = _member
       ) do
    Nostrum.Api.Guild.modify_member(guild_id, member_id, %{nick: nick, roles: roles})
  end
end
