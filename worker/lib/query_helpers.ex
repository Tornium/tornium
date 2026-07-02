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

defmodule Tornium.QueryHelpers do
  @moduledoc """
  Helper macros for Ecto queries.
  """

  @doc """
  Unnest data into an Ecto query.

  NOTE: This does not work with columns that are arrays as postgresql would flatten a nested array fully.
  """
  defmacro unnest(columns) do
    # We want to ensure that the provided columns are a map or a keyword list.
    columns =
      case columns do
        {:%{}, _, map_data} -> map_data
        list when is_list(list) -> list
        _ -> raise("unnest/1 expects a compile-time map or keyword list literal specifying column structures.")
      end

    num_args = length(columns)
    placeholders = Stream.duplicate("?", num_args) |> Enum.join(", ")
    col_names = Enum.map_join(columns, ", ", fn {col, _val} -> column_name(col) end)

    sql_string = "SELECT * FROM unnest(#{placeholders}) AS t(#{col_names})"
    ecto_args = Enum.map(columns, fn {_col, value} -> value end)

    quote do
      fragment(unquote(sql_string), unquote_splicing(ecto_args))
    end
  end

  defp column_name({name, _, _}) when is_atom(name), do: Atom.to_string(name)
  defp column_name(name) when is_atom(name), do: Atom.to_string(name)
end
