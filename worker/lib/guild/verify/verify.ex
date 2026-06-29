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
  @moduledoc """
  Module to process the verification of users according to a server's configuration and 
  the user's current roles and nick, the user's Torn/Discord ID, and the user's Torn
  data.
  """

  alias Tornium.Repo
  import Ecto.Query

  # TODO: Comment the private methods

  @typedoc """
  The state of the verification process after resolving the `MapSet` of roles into a list.
  """
  @type resolved_state() :: %{roles: [Tornium.Discord.role()], nick: String.t()}

  @type verification_errors() ::
          Nostrum.Error.ApiError.t()
          | Tornium.API.Error.t()
          | :unverified
          | :nochanges
          | :api_key
          | :exclusion_role
          | {:config, String.t()}

  @type verification_error() :: {:error, verification_errors(), Tornium.Schema.Server.t() | nil}

  @type verification_result() ::
          {:ok, Nostrum.Struct.Guild.Member.t(), Tornium.Schema.Server.t()} | verification_error()

  @doc """
  Verify a Discord member of a Discord server.

  ## Parameters
    - guild: The guild (or guild ID) the user should be verified for
    - member: Nostrum struct of the Discord member of the user

  ## Options
    * `:force?` - Force an update of the user's API data (default: `false`)
    * `:niceness` - Priority of the Tornex API call (default: `10`)

  ## Returns
    - OK with the updated member struct
    - Error with the error reason
  """
  @spec verify(
          guild :: pos_integer() | Tornium.Schema.Server.t(),
          member :: Nostrum.Struct.Guild.Member.t(),
          opts :: keyword()
        ) :: verification_result()
  def verify(guild, member, opts \\ [])

  def verify(guild, %Nostrum.Struct.Guild.Member{} = member, opts) when is_integer(guild) do
    Tornium.Schema.Server
    |> Repo.get(guild)
    |> verify(member, opts)
  end

  def verify({:error, error}, _member, _opts) do
    # Error passthrough from possible validation of server configuration
    {:error, error}
  end

  def verify(guild, %Nostrum.Struct.Guild.Member{} = _member, _opts) when is_nil(guild) do
    {:error, {:config, "invalid guild ID"}, nil}
  end

  def verify(%Tornium.Schema.Server{} = guild, %Nostrum.Struct.Guild.Member{} = member, opts) do
    if MapSet.size(MapSet.intersection(MapSet.new(member.roles), MapSet.new(guild.exclusion_roles))) > 0 do
      # Member has at least one exclusion role and should be skipped
      {:error, :exclusion_role, guild}
    else
      api_key = Tornium.Guild.get_random_admin_key(guild)

      case handle_guild(guild, api_key, member, opts) do
        {:ok, %Nostrum.Struct.Guild.Member{} = member} -> {:ok, member, guild}
        {:error, error} -> {:error, error, guild}
      end
    end
    |> log(member)
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
          {:ok, Nostrum.Struct.Guild.Member.t(), Tornium.Schema.Server.t()} | verification_error()
  def handle_on_join(guild_id, member) when is_integer(guild_id) do
    Repo.get(Tornium.Schema.Server, guild_id)
    |> validate_on_join()
    |> verify(member, force?: true, niceness: -10)
  end

  # TODO: Rename handle_guild to be more descriptive
  @spec handle_guild(
          guild :: Tornium.Schema.Server.t(),
          api_key :: Tornium.Schema.TornKey | nil,
          member :: Nostrum.Struct.Guild.Member.t(),
          opts :: keyword()
        ) :: {:ok, Nostrum.Struct.Guild.Member.t()} | {:error, verification_errors()}
  defp handle_guild(guild, api_key, member, opts \\ [])

  defp handle_guild(_guild, api_key, %Nostrum.Struct.Guild.Member{} = _member, _opts) when is_nil(api_key) do
    {:error, :api_key}
  end

  defp handle_guild(
         %Tornium.Schema.Server{} = guild,
         %Tornium.Schema.TornKey{} = api_key,
         %Nostrum.Struct.Guild.Member{user_id: member_id} = member,
         opts
       ) do
    case Tornium.Guild.Verify.Config.validate(guild) do
      {:error, reason} when is_binary(reason) ->
        {:error, {:config, String.downcase(reason)}}

      %Tornium.Guild.Verify.Config{} = config ->
        Tornium.User.update_by_id({:discord, member_id}, api_key,
          force: Keyword.get(opts, :force?, false),
          niceness: Keyword.get(opts, :niceness, 10)
        )
        |> build_changes(config, member)
        |> perform_changes(guild, member)
    end
  end

  @spec validate_changes_made(
          new_roles_nick :: Tornium.Guild.Verify.Logic.state(),
          original_roles :: [Tornium.Discord.role()],
          original_nick :: String.t() | nil
        ) ::
          resolved_state() | :nochanges
  defp validate_changes_made(%{roles: roles, nick: nick} = _new_roles_nick, original_roles, original_nick)
       when is_list(original_roles) do
    patched_map =
      %{roles: MapSet.to_list(roles), nick: nick}
      |> then(fn patched_map ->
        if Map.get(patched_map, :roles) == original_roles, do: Map.delete(patched_map, :roles), else: patched_map
      end)
      |> then(fn patched_map ->
        if Map.get(patched_map, :nick) == original_nick, do: Map.delete(patched_map, :nick), else: patched_map
      end)

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
        ) :: {:verified, resolved_state() | :nochanges} | Tornium.API.Error.t() | {:unverified, resolved_state()}
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
          changeset ::
            {:verified, resolved_state() | :nochanges} | {:unverified, resolved_state()} | Tornium.API.Error.t(),
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

  defp perform_changes(%Tornium.API.Error{} = error, _guild, _member) do
    {:error, error}
  end

  defp perform_changes({:verified, :nochanges}, _guild, _member) do
    {:error, :nochanges}
  end

  defp perform_changes(
         {:verified, changeset},
         %Tornium.Schema.Server{sid: guild_id} = _guild,
         %Nostrum.Struct.Guild.Member{user_id: member_id} = _member
       )
       when is_map(changeset) do
    Nostrum.Api.Guild.modify_member(guild_id, member_id, changeset)
  end

  @spec log(verification_result :: verification_result(), original_member :: Nostrum.Struct.Guild.Member.t()) ::
          verification_result()
  defp log(
         {:ok, %Nostrum.Struct.Guild.Member{nick: old_nickname, roles: old_roles} = _current_member,
          %Tornium.Schema.Server{sid: guild_id} = _guild} = verification_result,
         %Nostrum.Struct.Guild.Member{user_id: discord_id, nick: new_nickname, roles: new_roles} = _original_member
       )
       when old_nickname != new_nickname or old_roles != new_roles do
    roles_removed = old_roles -- new_roles
    roles_added = new_roles -- old_roles
    nickname_changed? = old_nickname != new_nickname

    # TODO: Use the same user ID as found earlier when building the changeset. However, currently
    # the code is not set up well to get that user ID out of the changeset's functions. This
    # would also need to be done for all the below log/2 functions.
    user_id =
      Tornium.Schema.User
      |> select([u], u.tid)
      |> where([u], u.discord_id == ^discord_id)
      |> Repo.one()

    :telemetry.execute([:tornium, :guild, :verify, :success], %{}, %{
      guild_id: guild_id,
      user_id: user_id,
      discord_id: discord_id,
      old_nickname: if(nickname_changed?, do: old_nickname, else: nil),
      new_nickname: if(nickname_changed?, do: new_nickname, else: nil),
      added_roles: roles_removed,
      removed_roles: roles_added
    })

    verification_result
  end

  defp log(
         {:error, %Nostrum.Error.ApiError{response: %{code: error_code}} = _error,
          %Tornium.Schema.Server{sid: guild_id} = _guild} = verification_result,
         %Nostrum.Struct.Guild.Member{user_id: discord_id} = _original_member
       ) do
    user_id =
      Tornium.Schema.User
      |> select([u], u.tid)
      |> where([u], u.discord_id == ^discord_id)
      |> Repo.one()

    # We don't want to log Discord's error messages as the basic message can be found in the
    # docs and the more in-depth message would likely use too much of the database's space.
    :telemetry.execute([:tornium, :guild, :verify, :failure], %{}, %{
      guild_id: guild_id,
      user_id: user_id,
      discord_id: discord_id,
      error_type: :discord_api,
      error_code: error_code,
      error_message: nil
    })

    verification_result
  end

  defp log(
         {:error, %Tornium.API.Error{code: error_code} = _error, %Tornium.Schema.Server{sid: guild_id} = _guild} =
           verification_result,
         %Nostrum.Struct.Guild.Member{user_id: discord_id} = _original_member
       ) do
    user_id =
      Tornium.Schema.User
      |> select([u], u.tid)
      |> where([u], u.discord_id == ^discord_id)
      |> Repo.one()

    :telemetry.execute([:tornium, :guild, :verify, :failure], %{}, %{
      guild_id: guild_id,
      user_id: user_id,
      discord_id: discord_id,
      error_type: :torn_api,
      error_code: error_code,
      error_message: nil
    })

    verification_result
  end

  defp log(
         {:error, :unverified = _error, %Tornium.Schema.Server{sid: guild_id} = _guild} = verification_result,
         %Nostrum.Struct.Guild.Member{user_id: discord_id} = _original_member
       ) do
    user_id =
      Tornium.Schema.User
      |> select([u], u.tid)
      |> where([u], u.discord_id == ^discord_id)
      |> Repo.one()

    :telemetry.execute([:tornium, :guild, :verify, :failure], %{}, %{
      guild_id: guild_id,
      user_id: user_id,
      discord_id: discord_id,
      error_type: :unverified,
      error_code: nil,
      error_message: nil
    })

    verification_result
  end

  # We don't care about logging the :nochanges error as it's not significant for the most part and would
  # result in a lot of spammy logs.

  defp log(
         {:error, :api_key = _error, %Tornium.Schema.Server{sid: guild_id} = _guild} = verification_result,
         %Nostrum.Struct.Guild.Member{user_id: discord_id} = _original_member
       ) do
    user_id =
      Tornium.Schema.User
      |> select([u], u.tid)
      |> where([u], u.discord_id == ^discord_id)
      |> Repo.one()

    :telemetry.execute([:tornium, :guild, :verify, :failure], %{}, %{
      guild_id: guild_id,
      user_id: user_id,
      discord_id: discord_id,
      error_type: :no_api_key,
      error_code: nil,
      error_message: nil
    })

    verification_result
  end

  # We don't care about logging the :exclusion_role error as it's purposefully done and would result in 
  # a lot of spammy logs.

  defp log(
         {:error, {:config, config_error_message} = _error, %Tornium.Schema.Server{sid: guild_id} = _guild} =
           verification_result,
         %Nostrum.Struct.Guild.Member{user_id: discord_id} = _original_member
       ) do
    user_id =
      Tornium.Schema.User
      |> select([u], u.tid)
      |> where([u], u.discord_id == ^discord_id)
      |> Repo.one()

    :telemetry.execute([:tornium, :guild, :verify, :failure], %{}, %{
      guild_id: guild_id,
      user_id: user_id,
      discord_id: discord_id,
      error_type: :no_api_key,
      error_code: nil,
      error_message: config_error_message
    })

    verification_result
  end

  defp log(
         verification_result,
         %Nostrum.Struct.Guild.Member{} = _original_member
       ) do
    # Passthrough for errors that we don't want to handle/log, errors that haven't been
    # properly handled above, and users that haven't been modified
    verification_result
  end
end
