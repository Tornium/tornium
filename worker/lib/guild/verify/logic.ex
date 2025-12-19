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

defmodule Tornium.Guild.Verify.Logic do
  @moduledoc """
  The logic funcitons for verifying a user.

  This module contains the functions required to modify the `state()` for each step of
  verifying a user regardless of whether the user is verified or unverified. Each
  verification step funciton either adds or removes roles depending on if they're valid
  for the user's faction, verification status, etc. or updates the user's nickname.
  """

  @typedoc """
  State of the verification logic.

  This stores the nickname and roles of the user being verified to be passed between the
  intermediate logic functions.
  """
  @type state :: %{roles: MapSet.t(Tornium.Discord.role()), nick: String.t()}

  # TODO: Determine if the type for new_values in the DB is actually String.t() or 
  # Tornium.Discord.role()
  @spec insert_update_roles(state :: state(), new_values :: [String.t()]) :: state()
  defp insert_update_roles(state, new_values) do
    # Inserts or updates the :roles key in the state for the list of roles. If there is
    # no :roles key, the new values will be used as the existing list of values. Otherwise,
    # the new values will be inserted into the existing list of roles (with duplicates
    # removed).
    Map.update(state, :roles, MapSet.new(new_values), fn existing_roles ->
      MapSet.union(existing_roles, MapSet.new(new_values))
    end)
  end

  @doc """
  Update a state map with a nickname for the user based on the server's configuration

  ## Parameters
    - state: State map
    - server_config: Server verification configuration struct
    - user: Ecto struct of the user to be verified

  ## Returns
    - State map
  """
  @spec set_verified_name(
          state :: state(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) :: state()
  def set_verified_name(
        state,
        %Tornium.Guild.Verify.Config{} = _server_config = %{verify_template: template},
        %Tornium.Schema.User{} = _user
      )
      when template == "" or is_nil(template) do
    state
  end

  def set_verified_name(
        state,
        %Tornium.Guild.Verify.Config{verify_template: template} = _server_config,
        %Tornium.Schema.User{} = user
      ) do
    verified_string =
      try do
        template
        |> Solid.parse!()
        |> Solid.render!(%{
          "name" => user.name,
          "tid" => to_string(user.tid),
          "tag" => user.faction.tag
        })
        |> Kernel.to_string()
        |> String.replace(["\n", "\t"], "")
      rescue
        _e in Solid.TemplateError ->
          "Template Error"

        _e in Solid.RenderError ->
          "Render Error"
      end

    Map.put(state, :nick, verified_string)
  end

  @doc """
  Update a state map with the verified roles for the user based on the server's configuration

  ## Parameters
    - state: State map
    - server_config: Server verification configuration struct
    - user: Ecto struct of the user to be verified

  ## Returns
    - State map
  """
  @spec set_verified_roles(
          state :: state(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) :: state()
  def(
    set_verified_roles(
      state,
      %Tornium.Guild.Verify.Config{verified_roles: roles} = _server_config,
      %Tornium.Schema.User{} = _user
    )
  ) do
    insert_update_roles(state, roles)
  end

  @doc """
  Updates a state map to remove verified roles that are invalid for users that are not verified based on the server's configuration.

  ## Parameters
    - state: State map
    - server_config: Server verificiation configuration struct
    - user: nil

  ## Returns
    - State map
  """
  @spec remove_invalid_verified_roles(state :: state(), server_config :: Tornium.Guild.Verify.Config.t(), user :: nil) ::
          state()
  def remove_invalid_verified_roles(
        state,
        %Tornium.Guild.Verify.Config{verified_roles: verified_roles} = _server_config,
        nil = _user
      ) do
    updated_roles =
      state
      |> Map.get(:roles)
      |> MapSet.difference(MapSet.new(verified_roles))

    Map.replace(state, :roles, updated_roles)
  end

  @doc """
  Update a state map with the unverified roles for a user that is not verified based on the server's configuration.

  ## Parameters
    - state: State map
    - server_config: Server verificiation configuration struct
    - user: nil

  ## Returns
    - State map
  """
  @spec set_unverified_roles(state :: state(), server_config :: Tornium.Guild.Verify.Config.t(), user :: nil) :: state()
  def set_unverified_roles(
        state,
        %Tornium.Guild.Verify.Config{unverified_roles: unverified_roles} = _server_config,
        user
      )
      when is_nil(user) do
    insert_update_roles(state, unverified_roles)
  end

  @doc """
  Updates a state map to remove unverified roles that are invalid for users that are verified based on the server's configuration.
  """
  @spec remove_invalid_unverified_roles(
          state :: state(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) :: state()
  def remove_invalid_unverified_roles(
        state,
        %Tornium.Guild.Verify.Config{unverified_roles: unverified_roles} = _server_config,
        %Tornium.Schema.User{} = _user
      ) do
    updated_roles =
      state
      |> Map.get(:roles)
      |> MapSet.difference(MapSet.new(unverified_roles))

    Map.replace(state, :roles, updated_roles)
  end

  @doc """
  Update a state map to remove the faction roles that are invalid for the user based on the server's configuration

  ## Parameters
    - state: State map
    - server_config: Server verification configuration struct
    - user: Ecto struct of the user to be verified or nil

  ## Returns
    - State map
  """
  @spec remove_invalid_faction_roles(
          state :: state(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t() | nil
        ) :: state()
  def remove_invalid_faction_roles(
        state,
        %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config,
        %Tornium.Schema.User{} = user
      ) do
    roles_to_remove =
      faction_verify
      |> Enum.flat_map(fn {faction_tid, _faction_verify_config = %{"roles" => faction_roles, "enabled" => enabled}} ->
        if String.to_integer(faction_tid) != user.faction.tid and enabled do
          faction_roles
        else
          []
        end
      end)
      |> MapSet.new()

    Map.replace(state, :roles, MapSet.difference(Map.get(state, :roles), roles_to_remove))
  end

  def remove_invalid_faction_roles(
        state,
        %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config,
        user
      )
      when is_nil(user) do
    roles_to_remove =
      faction_verify
      |> Enum.flat_map(fn {_faction_tid, _faction_verify_config = %{"roles" => faction_roles, "enabled" => enabled}} ->
        if enabled do
          faction_roles
        else
          []
        end
      end)
      |> MapSet.new()

    Map.replace(state, :roles, MapSet.difference(Map.get(state, :roles), roles_to_remove))
  end

  @spec can_set_faction_roles?(faction_verify :: state(), user :: Tornium.Schema.User.t()) :: boolean()
  defp can_set_faction_roles?(faction_verify, user) do
    faction_config = Map.get(faction_verify, Integer.to_string(user.faction.tid || 0), %{})
    Map.get(faction_config, "enabled", false)
  end

  @doc """
  Update a state map with the faction roles for the user based on the server's configuration

  ## Parameters
    - state: State map
    - server_config: Server verification configuration struct
    - user: Ecto struct of the user to be verified

  ## Returns
    - State map
  """
  @spec set_faction_roles(
          state :: state(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) ::
          state()
  def set_faction_roles(
        %{} = state,
        %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config,
        %Tornium.Schema.User{} = user
      ) do
    if can_set_faction_roles?(faction_verify, user) do
      roles =
        faction_verify
        |> Map.get(Integer.to_string(user.faction.tid))
        |> Map.get("roles")

      insert_update_roles(state, roles)
    else
      state
    end
  end

  @doc """
  Update a state map to remove the faction position roles that are invalid for the user based on the server's configuration

  ## Parameters
    - state: State map
    - server_config: Server verification configuration struct
    - user: Ecto struct of the user to be verified or nil

  ## Returns
    - State map
  """
  @spec remove_invalid_faction_position_roles(
          state :: state(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t() | nil
        ) :: state()
  def remove_invalid_faction_position_roles(
        state,
        %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config,
        %Tornium.Schema.User{} = user
      ) do
    roles_to_remove =
      faction_verify
      |> Enum.map(fn {_faction_tid, _faction_verify_config = %{"positions" => position_config, "enabled" => enabled}} ->
        Enum.map(position_config, fn {position_pid, position_roles} ->
          if user.faction_position_id == position_pid or not enabled do
            []
          else
            position_roles
          end
        end)
        |> List.flatten()
      end)
      |> List.flatten()
      |> MapSet.new()

    Map.replace(state, :roles, MapSet.difference(Map.get(state, :roles), roles_to_remove))
  end

  def remove_invalid_faction_position_roles(
        state,
        %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config,
        user
      )
      when is_nil(user) do
    roles_to_remove =
      faction_verify
      |> Enum.flat_map(fn {_faction_tid,
                           _faction_verify_config = %{"positions" => position_config, "enabled" => enabled}} ->
        Enum.flat_map(position_config, fn {_position_pid, position_roles} ->
          if enabled do
            position_roles
          else
            []
          end
        end)
      end)
      |> MapSet.new()

    Map.replace(state, :roles, MapSet.difference(Map.get(state, :roles), roles_to_remove))
  end

  @spec can_set_faction_position_roles?(faction_verify :: state(), user :: Tornium.Schema.User.t()) :: boolean()
  defp can_set_faction_position_roles?(faction_verify, user) do
    cond do
      user.faction.tid == 0 or is_nil(user.faction.tid) ->
        false

      is_nil(user.faction_position_id) ->
        false

      Map.get(faction_verify, Integer.to_string(user.faction.tid)) |> is_nil() ->
        false

      Map.get(faction_verify, Integer.to_string(user.faction.tid)) |> Map.get("enabled", false) == false ->
        false

      faction_verify
      |> Map.get(Integer.to_string(user.faction.tid))
      |> Map.get("positions", %{})
      |> Map.get(user.faction_position_id)
      |> is_nil() ->
        false

      true ->
        true
    end
  end

  @doc """
  Update a state map with the faction position roles for the user based on the server's configuration

  ## Parameters
    - state: State map
    - server_config: Server verification configuration struct
    - user: Ecto struct of the user to be verified

  ## Returns
    - State map
  """
  @spec set_faction_position_roles(
          state :: state(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) :: state()
  def set_faction_position_roles(
        state,
        %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config,
        %Tornium.Schema.User{} = user
      ) do
    if can_set_faction_position_roles?(faction_verify, user) do
      insert_update_roles(
        state,
        faction_verify
        |> Map.get(Integer.to_string(user.faction.tid))
        |> Map.get("positions")
        |> Map.get(user.faction_position_id)
      )
    else
      state
    end
  end
end
