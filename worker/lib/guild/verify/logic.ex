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

defmodule Tornium.Guild.Verify.Logic do
  @spec insert_update_roles(state :: map(), new_values :: List) :: map()
  defp insert_update_roles(state, new_values) do
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
  @spec set_verified_name(state :: map(), server_config :: Tornium.Guild.Verify.Config.t(), user :: Tornium.Schema.User.t()) ::
          map()
  def set_verified_name(state, %Tornium.Guild.Verify.Config{} = _server_config = %{verify_template: template}, %Tornium.Schema.User{} = _user)
      when template == "" or is_nil(template) do
    state
  end

  def set_verified_name(state, %Tornium.Guild.Verify.Config{verify_template: template} = _server_config, %Tornium.Schema.User{} = user) do
    verified_string =
      template
      |> String.replace("{{ name }}", user.name)
      |> String.replace("{{ tid }}", to_string(user.tid))
      |> String.replace("{{ tag }}", user.faction.tag)

    Map.put(state, "nick", verified_string)
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
          state :: map(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) :: map()
  def set_verified_roles(state, %Tornium.Guild.Verify.Config{verified_roles: roles} = _server_config, %Tornium.Schema.User{} = _user) do
    insert_update_roles(state, roles)
  end

  @doc """
  Update a state map to remove the faction roles that are invalid for the user based on the server's configuration

  ## Parameters
    - state: State map
    - server_config: Server verification configuration struct
    - user: Ecto struct of the user to be verified

  ## Returns
    - State map
  """
  @spec remove_invalid_faction_roles(
          state :: map(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) :: map()
  def remove_invalid_faction_roles(state, %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config, %Tornium.Schema.User{} = user) do
    roles_to_remove =
      faction_verify
      |> Enum.map(fn {faction_tid, _faction_verify_config = %{"roles" => faction_roles, "enabled" => enabled}} ->
        if String.to_integer(faction_tid) != user.faction.tid and enabled do
          faction_roles
        else
          []
        end
      end)
      |> List.flatten()
      |> MapSet.new()

    Map.replace(state, :roles, MapSet.difference(Map.get(state, :roles), roles_to_remove))
  end

  @spec can_set_faction_roles?(faction_verify :: map(), user :: Tornium.Schema.User.t()) :: boolean()
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
  @spec set_faction_roles(state :: map(), server_config :: Tornium.Guild.Verify.Config.t(), user :: Tornium.Schema.User.t()) ::
          map()
  def set_faction_roles(state, %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config, %Tornium.Schema.User{} = user) do
    if can_set_faction_roles?(faction_verify, user) do
      insert_update_roles(state, Map.get(Map.get(faction_verify, Integer.to_string(user.faction.tid)), "roles"))
    else
      state
    end
  end

  @doc """
  Update a state map to remove the faction position roles that are invalid for the user based on the server's configuration

  ## Parameters
    - state: State map
    - server_config: Server verification configuration struct
    - user: Ecto struct of the user to be verified

  ## Returns
    - State map
  """
  @spec remove_invalid_faction_position_roles(
          state :: map(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) :: map()
  def remove_invalid_faction_position_roles(state, %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config, %Tornium.Schema.User{} = user) do
    roles_to_remove =
      faction_verify
      |> Enum.map(fn {_faction_tid, _faction_verify_config = %{"positions" => position_config, "enabled" => enabled}} ->
        Enum.map(position_config, fn {position_pid, position_roles} ->
          if user.faction_position.pid == position_pid or not enabled do
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

  @spec can_set_faction_position_roles?(faction_verify :: map(), user :: Tornium.Schema.User.t()) :: boolean()
  defp can_set_faction_position_roles?(faction_verify, user) do
    cond do
      user.faction.tid == 0 or is_nil(user.faction.tid) ->
        false

      is_nil(user.faction_position) ->
        false

      Map.get(faction_verify, Integer.to_string(user.faction.tid)) |> is_nil() ->
        false

      Map.get(faction_verify, Integer.to_string(user.faction.tid)) |> Map.get("enabled", false) == false ->
        false

      Map.get(faction_verify, Integer.to_string(user.faction.tid))
      |> Map.get("positions", %{})
      |> Map.get(user.faction_position.pid)
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
          state :: map(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User.t()
        ) :: map()
  def set_faction_position_roles(state, %Tornium.Guild.Verify.Config{faction_verify: faction_verify} = _server_config, %Tornium.Schema.User{} = user) do
    if can_set_faction_position_roles?(faction_verify, user) do
      insert_update_roles(
        state,
        Map.get(faction_verify, Integer.to_string(user.faction.tid))
        |> Map.get("positions")
        |> Map.get(user.faction_position.pid)
      )
    else
      state
    end
  end
end
