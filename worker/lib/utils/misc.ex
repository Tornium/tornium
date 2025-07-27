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

defmodule Tornium.Utils do
  @moduledoc """
  Collection of utility functions.
  """

  @doc """
  Convert a string to an integer. Return nil if the value can not be converted to an integer.
  """
  @spec string_to_integer(string :: String.t()) :: integer() | nil
  def string_to_integer(string) do
    try do
      String.to_integer(string)
    rescue
      ArgumentError -> nil
    end
  end

  @doc """
  Create a string of role mentions from a list of Discord roles.

  If a role is an assignable role, the assignable role will be replaced with the roles provided in `opts.assigns`
  if provided. If no `assigns` are provided, the assignable role will not be included in the created string of 
  role mentions.

  ## Options
    * `:assigns` - List of role IDs or `{:user, user Discord ID}`
  """
  @spec roles_to_string(roles :: [Tornium.Discord.role_assignable()], opts :: keyword()) :: String.t()
  def roles_to_string(roles, opts \\ []) when is_list(roles) do
    # TODO: This and `set_assigned_role` should be under Tornium.Discord
    # TODO: Test this
    roles
    |> Enum.uniq()
    |> set_assigned_role(opts)
    |> List.flatten()
    |> Enum.reject(&is_nil/1)
    |> Enum.map_join(" ", fn
      role_id when is_integer(role_id) -> "<@&#{role_id}>"
      {:user, user_id} when is_integer(user_id) -> "<@#{user_id}>"
    end)
  end

  @spec set_assigned_role(roles :: [Tornium.Discord.role_assignable()], opts :: keyword()) :: [Tornium.Discord.role()]
  defp set_assigned_role(roles, opts) do
    assigns = Keyword.get(opts, :assigns, [])

    if Enum.member?(roles, -1) do
      Enum.map(roles, fn
        -1 -> assigns
        role -> role
      end)
    else
      roles
    end
  end

  @doc """
  Recursively create a map from group of tuples (used by Tornium.Lua).
  """
  @spec tuples_to_map(data :: list(tuple())) :: map()
  def tuples_to_map(data) when is_list(data) do
    # TODO: Test this

    Enum.map(data, fn
      {key, value} when is_list(value) ->
        {key, tuples_to_map(value)}

      {key, value} ->
        {key, value}
    end)
    |> Map.new()
  end

  # TODO: Document function
  @spec unix_to_timestamp(timestamp :: integer() | nil) :: DateTime.t() | nil
  def unix_to_timestamp(timestamp, unit \\ :second)

  def unix_to_timestamp(timestamp, unit) when is_integer(timestamp) do
    DateTime.from_unix!(timestamp, unit)
  end

  def unix_to_timestamp(_timestamp, _unit) do
    nil
  end
end
