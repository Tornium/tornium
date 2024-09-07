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
  @spec insert_update_roles(state :: map(), new_values :: List) :: map()
  defp insert_update_roles(state, new_values) do
    Map.update(state, :roles, MapSet.new(new_values), fn existing_roles ->
      MapSet.union(existing_roles, MapSet.new(new_values))
    end)
    |> IO.inspect()
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

    # TODO: Add support for faction tags

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

  @spec remove_invalid_faction_roles(state :: map(), server_config :: Tornium.Guild.Verify.Config.t(), user :: Tornium.Schema.User) :: map()
  def remove_invalid_faction_roles(state, _server_config = %{faction_verify: faction_verify}, user) do
    # {"37537": {"roles": [1097494763093098526], "positions": {}, "enabled": true}}

    Enum.each(
      faction_verify,
      fn {faction_tid, faction_verify_config} -> if Integer.parse(faction_tid) != user.faction.tid do Map.update!(state, :roles, MapSet.difference(Map.get(state, :roles), faction_verify_config["roles"])) end end
    )
  end

  # faction_id: int
  # verify_data: dict
  # for verify_faction_id, verify_data in faction_verify.items():
  #     if int(verify_faction_id) == faction_id:
  #         continue

  #     roles.update(set(str(role) for role in verify_data.get("roles", tuple())))
end
