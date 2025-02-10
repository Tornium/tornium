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
  """
  @spec roles_to_string(roles :: list(String.t() | integer())) :: binary()
  def roles_to_string(roles) when is_list(roles) do
    roles
    |> Enum.map(&"<@&#{&1}>")
    |> Enum.join(" ")
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

  @spec unix_to_timestamp(timestamp :: integer() | nil) :: DateTime.t() | nil
  def unix_to_timestamp(timestamp, unit \\ :second)

  def unix_to_timestamp(timestamp, unit) when is_integer(timestamp) do
    DateTime.from_unix!(timestamp, unit)
  end

  def unix_to_timestamp(_timestamp, _unit) do
    nil
  end
end
