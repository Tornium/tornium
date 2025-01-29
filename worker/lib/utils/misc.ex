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

defmodule Tornium.Utils do
  # TODO: Add documentation
  @spec string_to_integer(string :: String.t()) :: integer() | nil
  def string_to_integer(string) do
    try do
      String.to_integer(string)
    rescue
      ArgumentError -> nil
    end
  end

  @spec roles_to_string(roles :: list(String.t() | integer())) :: binary()
  def roles_to_string(roles) when is_list(roles) do
    roles
    |> Enum.map(&"<@&#{&1}>")
    |> Enum.join(" ")
  end

  @spec tuples_to_map(data :: list(tuple())) :: map()
  def tuples_to_map(data) when is_list(data) do
    Enum.map(data, fn
      {key, value} when is_list(value) ->
        {key, tuples_to_map(value)}

      {key, value} ->
        {key, value}
    end)
    |> Map.new()
  end
end
