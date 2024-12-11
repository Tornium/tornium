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

defmodule Tornium.Lua do
  # This timeout is double that of the default Lua VM timeout to allow for delays with the supervisor
  @lua_supervisor_timeout 200

  @doc """
  Execute Lua code inside of a sandbox using Luerl through the Tornium.LuaSupervisor supervisor

  ## Parameters
    - code: A string of Lua code to be executed
    - input_state: A keyword list of values to be added to the Lua VM's state

  ## Returns
    - OK with executed code's return value
    - LuaError when there's an error within the Lua VM
    - Error with the error reason (e.g. timeout)
  """
  @spec execute_lua(code :: String.t(), input_state :: Keyword) ::
          {:error, atom()} | {:ok, List} | {:lua_error, any()}
  def execute_lua(code, input_state \\ []) when is_binary(code) do
    # TODO: Add tests for this
    # TODO: Update typespec for `execute_lua` based on https://github.com/elixir-lang/elixir/pull/12482/commits/bf78c78a9ef77c4d679bbda0e03db17152321fc5
    state = :luerl_sandbox.init()

    state =
      Enum.reduce(input_state, state, fn {key, value}, accumulated_state ->
        :luerl.set_table([key], value, accumulated_state)
      end)

    task =
      Task.Supervisor.async(Tornium.LuaSupervisor, fn ->
        # Default timeout of 100ms in Lua VM
        # See https://github.com/rvirding/luerl/blob/37991d1692ad543eb0cb67faf515e6105c6ae79f/src/luerl_sandbox.erl#L79 for list of options
        :luerl_sandbox.run(code, state)
      end)

    case Task.yield(task, @lua_supervisor_timeout) || Task.shutdown(task) do
      {:ok, {[triggered?, render_table, passthrough_state] = _ret, state}} ->
        render_state =
          render_table
          |> :luerl.decode(state)
          |> Tornium.Utils.tuples_to_map()
          |> IO.inspect()

        # TODO: Generate Liquid-templated embed from render_state
        {:ok, {triggered?, render_state, passthrough_state}}

      {:ok, {:error, :timeout}} ->
        {:error, :timeout}

      {:ok, {:error, {:lau_error, error, _state}}} ->
        # TODO: Determine type of error for typespec
        {:lua_error, error}

      {:exit, reason} ->
        # TODO: Determine type of error for typespec
        {:error, reason}

      nil ->
        {:error, :timeout}
    end
  end
end
