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

defmodule Tornium.Lua do
  # TODO: Redo this comment
  # This timeout is double that of the default Lua VM timeout to allow for delays with the supervisor
  @lua_supervisor_timeout 1000

  # TODO: Update naming to make this code more generic

  @type trigger_return() ::
          {:ok, [triggered?: boolean(), render_state: map(), passthrough_state: map()]}
          | {:error, any()}
          | {:lua_error, any()}

  @doc """
  Execute Lua code inside of a sandbox using Luerl through the Tornium.LuaSupervisor supervisor

  ## Parameters
    - code: A string of Lua code to be executed
    - input_state: A map of values to be added to the Lua VM's state

  ## Returns
    - OK with executed code's return value
    - LuaError when there's an error within the Lua VM
    - Error with the error reason (e.g. timeout)
  """
  @spec execute_lua(code :: String.t(), input_state :: map()) :: trigger_return()
  def execute_lua(code, input_state \\ %{}) when is_binary(code) do
    # TODO: Add tests for this
    state = :luerl_sandbox.init()

    state =
      Enum.reduce(input_state, state, fn {key, value}, accumulated_state ->
        :luerl.set_table([key], value, accumulated_state)
      end)

    task =
      Task.Supervisor.async(Tornium.LuaSupervisor, fn ->
        # Default timeout of 100ms in Lua VM
        # See https://github.com/rvirding/luerl/blob/37991d1692ad543eb0cb67faf515e6105c6ae79f/src/luerl_sandbox.erl#L79 for list of options
        :luerl_sandbox.run(code, %{max_time: @lua_supervisor_timeout}, state)
      end)

    case Task.yield(task, @lua_supervisor_timeout) || Task.shutdown(task) do
      {:ok, {[triggered?, render_table, passthrough_table] = _ret, state}} ->
        render_state =
          render_table
          |> :luerl.decode(state)
          |> Tornium.Utils.tuples_to_map()

        passthrough_state =
          passthrough_table
          |> :luerl.decode(state)
          |> Tornium.Utils.tuples_to_map()

        {:ok, [triggered?: triggered?, render_state: render_state || %{}, passthrough_state: passthrough_state || %{}]}

      {:ok, {:error, :timeout}} ->
        {:error, :timeout}

      {:ok, {:error, {:lua_error, error, state}}} ->
        # TODO: Determine type of error for typespec
        IO.inspect(error)
        IO.inspect(:luerl.get_stacktrace(state))
        {:lua_error, error}

      {:exit, reason} ->
        # TODO: Determine type of error for typespec
        {:error, reason}

      nil ->
        {:error, :supervisor_timeout}
    end
  end
end
