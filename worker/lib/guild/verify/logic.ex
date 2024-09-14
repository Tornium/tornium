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

  @spec set_verified_name(state :: map(), server_config :: Tornium.Guild.Verify.Config.t(), user :: Tornium.Schema.User) ::
          map()
  def set_verified_name(state, _server_config = %{verify_template: template}, _user)
      when template == "" or is_nil(template) do
    state
  end

  def set_verified_name(state, _server_config = %{verify_template: template}, user) do
    verified_string =
      template
      |> String.replace("{{ name }}", user.name)
      |> String.replace("{{ tid }}", to_string(user.tid))
      |> String.replace("{{ tag }}", user.faction.tag)

    Map.put(state, "nick", verified_string)
  end

  @spec set_verified_roles(
          state :: map(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User
        ) :: map()
  def set_verified_roles(state, _server_config = %{verified_roles: roles}, _user) do
    insert_update_roles(state, roles)
  end

  @spec remove_invalid_faction_roles(
          state :: map(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User
        ) :: map()
  def remove_invalid_faction_roles(state, _server_config = %{faction_verify: faction_verify}, user) do
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

  @spec can_set_faction_roles?(faction_verify :: map(), user :: Tornium.Schema.User) :: boolean()
  defp can_set_faction_roles?(faction_verify, user) do
    faction_config = Map.get(faction_verify, Integer.to_string(user.faction.tid || 0), %{})
    Map.get(faction_config, "enabled", false)
  end

  @spec set_faction_roles(state :: map(), server_config :: Tornium.Guild.Verify.Config.t(), user :: Tornium.Schema.User) ::
          map()
  def set_faction_roles(state, _server_config = %{faction_verify: faction_verify}, user) do
    if can_set_faction_roles?(faction_verify, user) do
      insert_update_roles(state, Map.get(Map.get(faction_verify, Integer.to_string(user.faction.tid)), "roles"))
    else
      state
    end
  end

  @spec remove_invalid_faction_position_roles(
          state :: map(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User
        ) :: map()
  def remove_invalid_faction_position_roles(state, _server_config = %{faction_verify: faction_verify}, user) do
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

  @spec can_set_faction_position_roles?(faction_verify :: map(), user :: Tornium.Schema.User) :: boolean()
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

  @spec set_faction_position_roles(
          state :: map(),
          server_config :: Tornium.Guild.Verify.Config.t(),
          user :: Tornium.Schema.User
        ) :: map()
  def set_faction_position_roles(state, _server_config = %{faction_verify: faction_verify}, user) do
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

  #     for verify_faction_id, faction_positions_data in faction_verify.items():
  #         if int(verify_faction_id) == faction_id:
  #             continue
  # 
  #         for position_uuid, position_roles in faction_positions_data.get("positions", {}).items():
  #             if position is not None and position_uuid == str(position.pid):
  #                 continue
  # 
  #             roles.update(set(str(role) for role in position_roles))
end
