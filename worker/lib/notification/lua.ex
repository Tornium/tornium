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

defmodule Tornium.Notification.Lua do
  @moduledoc """
  A Lua VM used to execute notification code.
  """

  @lua_supervisor_timeout 1000

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
    state = setup_vm(input_state)
    execution_task = Task.Supervisor.async(Tornium.LuaSupervisor, fn -> Lua.eval!(state, code) end)
    execution_result = Task.yield(execution_task, @lua_supervisor_timeout) || Task.shutdown(execution_task)
    handle_execution_result(execution_result)
  end

  @doc """
  Set up a sandboxed Lua VM with necessary data and functions injected into it.
  """
  @spec setup_vm(input_state :: map()) :: Lua.t()
  def setup_vm(input_state \\ %{}) when is_map(input_state) do
    input_state
    |> Enum.reduce(Lua.new(), fn {key, value}, accumulated_state -> Lua.set!(accumulated_state, [key], value) end)
    |> Lua.load_api(Tornium.Notification.Lua.API)
  end

  @doc """
  Handle the result of the Lua execution and reformat it into Elixir-friendly data types.
  """
  @spec handle_execution_result(result :: {:ok, term()} | {:exit, term()} | nil) :: trigger_return()
  def handle_execution_result({:ok, {[triggered?, render_table, passthrough_table], %Lua{} = _state}})
      when is_boolean(triggered?) do
    render_state = Tornium.Utils.tuples_to_map(render_table)
    passthrough_state = Tornium.Utils.tuples_to_map(passthrough_table)

    {:ok, [triggered?: triggered?, render_state: render_state, passthrough_state: passthrough_state]}
  end

  def handle_execution_result({:ok, {:error, :timeout}}) do
    {:error, :timeout}
  end

  def handle_execution_result({:ok, {:error, {:lua_error, error, state}}}) do
    IO.inspect(error, label: "Lua error")
    IO.inspect(:luerl.get_stacktrace(state), label: "Lua stacktrace")
    {:lua_error, error}
  end

  def handle_execution_result({:exit, reason}), do: {:error, reason}
  def handle_execution_result(result) when is_nil(result), do: {:error, :supervisor_timeout}
  # TODO: Improve handling of errors from Lua errors from the Elixir lua library
  # The lua library raises an exception instead of returning an error tuple as Luerl did.
end
