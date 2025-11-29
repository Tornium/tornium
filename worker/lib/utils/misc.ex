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

  ## Examples

    iex> string_to_integer("not an integer")
    nil

    iex> string_to_integer("100")
    100

    iex> string_to_integer("10.01")
    nil
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
  Recursively create a map from group of tuples (used by `Tornium.Lua`).

  ## Examples

    iex> tuples_to_map([
    ...>   {"one", 1},
    ...>   {"two", 2},
    ...>   {"three", 3}
    ...> ])
    %{"one" => 1, "two" => 2, "three" => 3}

    iex> tuples_to_map([
    ...>   {:foo, "foo"},
    ...>   {:bar, "bar"}
    ...> ])
    %{foo: "foo", bar: "bar"}
  """
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

  @doc """
  Convert a UNIX timestamp to a DateTime struct.

  If the timestamp is `nil`, `nil` will be returned.
  """
  @spec unix_to_timestamp(timestamp :: integer() | nil) :: DateTime.t() | nil
  def unix_to_timestamp(timestamp, unit \\ :second)

  def unix_to_timestamp(timestamp, unit) when is_integer(timestamp) do
    DateTime.from_unix!(timestamp, unit)
  end

  def unix_to_timestamp(_timestamp, _unit) do
    nil
  end

  @doc """
  Format an integer with commas as the thousands separator.

  ## Examples

    iex> commas(1_234_567)
    "1,234,567"
  """
  @spec commas(value :: integer()) :: String.t()
  def commas(value) when is_integer(value) do
    value
    |> Integer.to_charlist()
    |> Enum.reverse()
    |> Enum.chunk_every(3)
    |> Enum.map(&Enum.reverse/1)
    |> Enum.reverse()
    |> Enum.join(",")
  end
end
